# Copyright 2026 Cetmix OU
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import hashlib
import logging
from itertools import groupby

import psycopg2

from odoo import _, api, models
from odoo.exceptions import AccessError, UserError
from odoo.osv.expression import AND

from odoo.addons.queue_job.delay import chain
from odoo.addons.queue_job.job import ENQUEUED, PENDING, STARTED, WAIT_DEPENDENCIES

_logger = logging.getLogger(__name__)

# Tautology to include field-linked attachments in searches.
# Odoo's ir.attachment._search adds ('res_field', '=', False) by default.
RES_FIELD_DOMAIN = ["|", ("res_field", "=", False), ("res_field", "!=", False)]

# Identity keys use this prefix so a second run can detect in-flight jobs
# for the same target storage (queue_job only dedups pending/enqueued).
S3_MIGRATION_IDENTITY_PREFIX = "s3-migration-"

PENDING_MIGRATION_STATES = (
    WAIT_DEPENDENCIES,
    PENDING,
    ENQUEUED,
    STARTED,
)


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    def _get_storage_force_db_config(self):
        """Honor the target storage when building force-DB rules.

        Core reads rules for ``_storage()`` (the database default). Migration
        must apply the *target* storage's ``force_db_for_default_attachment_rules``,
        passed via ``s3_migration_storage_code`` in the context.
        """
        storage_code = self.env.context.get("s3_migration_storage_code")
        if storage_code:
            return self.env["fs.storage"].get_force_db_for_default_attachment_rules(
                storage_code
            )
        return super()._get_storage_force_db_config()

    @api.model
    def _s3_migration_domain(self, storage_code):
        """Build domain for attachments eligible for migration."""
        base = [
            ("checksum", "!=", False),
            ("type", "=", "binary"),
            ("store_fname", "!=", False),
            ("store_fname", "not like", f"{storage_code}://%"),
            # DB-stored attachments are never migrated; they may still be
            # used as data donors in ``_get_binary_data_for_checksum``.
            ("db_datas", "=", False),
        ] + RES_FIELD_DOMAIN

        fs_storage = self.env["fs.storage"].sudo().get_by_code(storage_code)
        if fs_storage and fs_storage.migration_use_storage_force_db_rules:
            force_db_domain = self._s3_get_force_db_domain(storage_code)
            if force_db_domain:
                return AND([base, ["!"] + force_db_domain])
        return base

    @api.model
    def _s3_get_force_db_domain(self, storage_code):
        """Domain for attachments that must stay in DB.

        Delegates to
        ``fs_attachment.ir.attachment._store_in_db_instead_of_object_storage_domain``
        so rule evaluation stays in sync with core. The target storage's rules
        are selected via ``s3_migration_storage_code`` (see
        ``_get_storage_force_db_config``).
        """
        return self.with_context(
            s3_migration_storage_code=storage_code
        )._store_in_db_instead_of_object_storage_domain()

    def _mark_old_store_fname_for_gc(self, old_fname):
        """Queue the previous remote object for garbage collection.

        Only files stored on an ``fs.storage`` are queued, through ``fs.file.gc``.
        Local filestore paths are left untouched: they are collected outside Odoo
        and are deliberately not added to the core checklist.
        """
        if self._is_file_from_a_storage(old_fname):
            self._fs_mark_for_gc(old_fname)

    def _get_binary_data_for_checksum(self, checksum, storage_code):
        """Get binary data for a checksum from any available source."""
        # Priority 1: Already migrated to target S3 (read from S3)
        domain = AND(
            [
                [
                    ("checksum", "=", checksum),
                    ("store_fname", "=like", f"{storage_code}://%"),
                ],
                RES_FIELD_DOMAIN,
            ]
        )
        donor = self.with_context(prefetch_fields=False).search(domain, limit=1)
        if donor:
            try:
                return donor.raw
            except OSError as e:
                _logger.debug("Failed to read from S3 donor %s: %s", donor.id, e)

        # Priority 2: Stored in DB (fast, no file access)
        domain = AND(
            [[("checksum", "=", checksum), ("db_datas", "!=", False)], RES_FIELD_DOMAIN]
        )
        donor = self.with_context(prefetch_fields=False).search(domain, limit=1)
        if donor:
            try:
                return donor.raw
            except OSError as e:
                _logger.debug("Failed to read from DB donor %s: %s", donor.id, e)

        # Priority 3: Local filestore (fallback)
        domain = AND([[("checksum", "=", checksum)], RES_FIELD_DOMAIN])
        candidates = self.with_context(prefetch_fields=False).search(domain, limit=5)
        for candidate in candidates:
            try:
                data = candidate.raw
                if data is not None:
                    return data
            except OSError:
                continue
        return None

    def _upload_to_storage(self, storage_code, bin_data, mimetype=None):
        """Write ``bin_data`` through the core storage write path.

        If an object already exists at the checksum path with the same size,
        skip the write (cheap size-based dedup shortcut, not a content
        comparison). Otherwise delegate to ``_storage_file_write`` so backend
        write options (S3 ContentType), directory creation and GC registration
        stay with ``fs_attachment``.
        """
        fs = self._get_fs_storage_for_code(storage_code)
        path = self._get_fs_path(storage_code, bin_data)
        fname = f"{storage_code}://{path}"
        expected_size = len(bin_data)

        if fs.exists(path):
            try:
                existing_size = fs.info(path).get("size", -1)
                if existing_size == expected_size:
                    return fname
                _logger.warning(
                    "Existing file %s has mismatched size (%d vs %d), overwriting",
                    path,
                    existing_size,
                    expected_size,
                )
            except OSError as e:
                _logger.debug("Cannot check existing file %s: %s, overwriting", path, e)

        return self.with_context(
            storage_location=storage_code,
            mimetype=mimetype,
        )._storage_file_write(bin_data)

    @api.model
    def _s3_migration_identity_key(self, storage_code, ids):
        """Deterministic identity key for a migration batch."""
        digest = hashlib.sha1(
            ",".join(str(i) for i in sorted(ids)).encode()
        ).hexdigest()
        return f"{S3_MIGRATION_IDENTITY_PREFIX}{storage_code}-{digest}"

    @api.model
    def _s3_has_pending_migration_jobs(self, storage_code):
        """Return True if a migration for ``storage_code`` is still running."""
        return bool(
            self.env["queue.job"]
            .sudo()
            .search_count(
                [
                    ("model_name", "=", "ir.attachment"),
                    ("method_name", "=", "s3_migrate_batch"),
                    (
                        "identity_key",
                        "=like",
                        f"{S3_MIGRATION_IDENTITY_PREFIX}{storage_code}-%",
                    ),
                    ("state", "in", list(PENDING_MIGRATION_STATES)),
                ]
            )
        )

    @api.model
    def _s3_pack_checksum_batches(self, rows, batch_size):
        """Pack ``{id, checksum}`` rows into batches that never split a group.

        A checksum group larger than ``batch_size`` becomes its own batch.
        ``rows`` must already be ordered by checksum.
        """
        batches = []
        current = []
        current_size = 0
        for _checksum, group in groupby(rows, key=lambda row: row["checksum"]):
            group_ids = [row["id"] for row in group]
            group_size = len(group_ids)
            if current and current_size + group_size > batch_size:
                batches.append(current)
                current = []
                current_size = 0
            current.extend(group_ids)
            current_size += group_size
            if current_size >= batch_size:
                batches.append(current)
                current = []
                current_size = 0
        if current:
            batches.append(current)
        return batches

    def _s3_check_migration_admin(self):
        if not self.env.user._is_admin():
            raise AccessError(_("Only administrators can execute this action."))

    @api.model
    def _s3_enqueue_migration(
        self,
        storage_code,
        batch_size=500,
        max_batches=None,
        channel="root.s3_migration",
        max_retries=None,
    ):
        """Enqueue checksum-grouped, chained migration jobs."""
        self._s3_check_migration_admin()
        if batch_size <= 0:
            raise UserError(_("Batch size must be greater than 0."))
        if max_batches is not None and max_batches < 0:
            raise UserError(_("Max batches cannot be negative."))
        if self._s3_has_pending_migration_jobs(storage_code):
            raise UserError(
                _(
                    "A migration is already running for storage %(code)s.",
                    code=storage_code,
                )
            )

        domain = self._s3_migration_domain(storage_code)
        force_db_config = self.env[
            "fs.storage"
        ].get_force_db_for_default_attachment_rules(storage_code)
        if force_db_config:
            _logger.info(
                "Migration will exclude force-DB files: %s",
                force_db_config,
            )

        rows = self.search_read(domain, ["checksum"], order="checksum, id")
        batches = self._s3_pack_checksum_batches(rows, batch_size)
        if max_batches:
            batches = batches[:max_batches]

        _logger.info(
            "Starting migration enqueue for storage %s "
            "(batch_size=%d, max_batches=%s, batches=%d)",
            storage_code,
            batch_size,
            max_batches or "unlimited",
            len(batches),
        )

        delayables = []
        total_enqueued = 0
        for batch_ids in batches:
            delayables.append(
                self.browse(batch_ids)
                .delayable(
                    channel=channel,
                    max_retries=max_retries,
                    identity_key=self._s3_migration_identity_key(
                        storage_code, batch_ids
                    ),
                )
                .s3_migrate_batch(storage_code)
            )
            total_enqueued += len(batch_ids)

        if delayables:
            chain(*delayables).delay()

        _logger.info(
            "Completed migration enqueue: %d attachments in %d batches for storage %s",
            total_enqueued,
            len(batches),
            storage_code,
        )
        return total_enqueued

    def _s3_lock_attachment_or_skip(self):
        """Lock this row with FOR UPDATE NOWAIT.

        Return True if the lock was acquired. If another transaction holds the
        lock, skip this attachment instead of failing the whole batch.
        """
        self.ensure_one()
        try:
            with self.env.cr.savepoint():
                self.env.cr.execute(
                    "SELECT id FROM ir_attachment WHERE id = %s FOR UPDATE NOWAIT",
                    (self.id,),
                    log_exceptions=False,
                )
            return True
        except psycopg2.OperationalError:
            _logger.info(
                "Attachment %s is locked by another transaction, skipping", self.id
            )
            return False

    def s3_migrate_batch(self, storage_code):
        """Migrate batch with checksum deduplication."""
        if not self:
            return True

        fs_storage = self.env["fs.storage"].sudo().get_by_code(storage_code)
        if not fs_storage:
            _logger.error("Storage not found: %s", storage_code)
            return False

        force_db_domain = []
        if fs_storage.migration_use_storage_force_db_rules:
            force_db_domain = self._s3_get_force_db_domain(storage_code)

        checksum_groups = {}
        for att in self:
            if att.checksum:
                checksum_groups.setdefault(att.checksum, self.env["ir.attachment"])
                checksum_groups[att.checksum] |= att

        total = len(self)
        migrated = 0
        skipped = 0

        _logger.info(
            "Starting batch: %d attachments (%d unique checksums) to %s",
            total,
            len(checksum_groups),
            storage_code,
        )

        for checksum, attachments in checksum_groups.items():
            representative = attachments[0]

            if force_db_domain and representative.filtered_domain(force_db_domain):
                skipped += len(attachments)
                continue

            bin_data = self._get_binary_data_for_checksum(checksum, storage_code)
            if bin_data is None:
                _logger.warning(
                    "No data for checksum %s, skipping %d attachments",
                    checksum,
                    len(attachments),
                )
                skipped += len(attachments)
                continue

            new_store_fname = self._upload_to_storage(
                storage_code, bin_data, mimetype=representative.mimetype
            )

            migrated_atts = self.env["ir.attachment"]
            for att in attachments:
                old_fname = att.store_fname
                if not att._s3_lock_attachment_or_skip():
                    skipped += 1
                    continue
                att.invalidate_recordset(["checksum", "store_fname"])
                if att.checksum != checksum or att.store_fname != old_fname:
                    skipped += 1
                    continue
                if old_fname and not old_fname.startswith(f"{storage_code}://"):
                    self._mark_old_store_fname_for_gc(old_fname)
                att._force_write_store_fname(new_store_fname)
                migrated_atts |= att

            if migrated_atts:
                migrated_atts._enforce_meaningful_storage_filename()
                migrated += len(migrated_atts)

            if migrated and migrated % 100 == 0:
                _logger.info(
                    "Batch progress: %d/%d migrated, %d skipped",
                    migrated,
                    total,
                    skipped,
                )

        _logger.info(
            "Batch complete: migrated=%d, skipped=%d (total=%d) to %s",
            migrated,
            skipped,
            total,
            storage_code,
        )
        return True
