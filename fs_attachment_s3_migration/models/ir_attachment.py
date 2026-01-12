# Copyright 2025 Cetmix OU
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models
from odoo.osv.expression import AND, OR

_logger = logging.getLogger(__name__)

# Tautology to include field-linked attachments in searches.
# Odoo's ir.attachment._search adds ('res_field', '=', False) by default.
RES_FIELD_DOMAIN = ["|", ("res_field", "=", False), ("res_field", "!=", False)]


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    @api.model
    def _s3_migration_domain(self, storage_code):
        """Build domain for attachments eligible for migration."""
        base = [
            ("checksum", "!=", False),
            ("type", "=", "binary"),
            ("store_fname", "!=", False),
            ("store_fname", "not like", f"{storage_code}://%"),
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
        """Get domain for attachments that must stay in DB."""
        force_db_rules = self.env[
            "fs.storage"
        ].get_force_db_for_default_attachment_rules(storage_code)
        if not force_db_rules:
            return []

        domain = None
        for mimetype_key, size_limit in force_db_rules.items():
            rule_domain = [("mimetype", "=like", f"{mimetype_key}%")]
            if size_limit:
                rule_domain = AND([rule_domain, [("file_size", "<=", size_limit)]])
            domain = OR([domain, rule_domain]) if domain else rule_domain

        return domain or []

    @api.model
    def _should_force_db(self, mimetype, file_size, force_db_rules):
        """Check if attachment should stay in DB based on force_db rules."""
        if not force_db_rules:
            return False
        mimetype = mimetype or ""
        file_size = file_size or 0
        for mime_prefix, limit in force_db_rules.items():
            if mimetype.startswith(mime_prefix):
                if limit == 0 or file_size <= limit:
                    return True
        return False

    @api.model
    def _compute_s3_path(self, checksum, optimize_path):
        """Compute S3 storage path for a given checksum."""
        if optimize_path:
            return f"{checksum[:2]}/{checksum[2:4]}/{checksum}"
        return checksum

    @api.model
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
                if data:
                    return data
            except OSError:
                continue
        return None

    def _upload_to_storage(self, fs, path, bin_data):
        """Upload binary data to storage with content verification."""
        dirname = "/".join(path.split("/")[:-1])
        if dirname:
            try:
                fs.makedirs(dirname, exist_ok=True)
            except OSError as e:
                _logger.debug("Directory %s may already exist: %s", dirname, e)

        expected_size = len(bin_data)

        if fs.exists(path):
            try:
                existing_size = fs.info(path).get("size", -1)
                if existing_size == expected_size:
                    return
                _logger.warning(
                    "Existing file %s has mismatched size (%d vs %d), overwriting",
                    path,
                    existing_size,
                    expected_size,
                )
            except OSError as e:
                _logger.debug(
                    "Cannot verify existing file %s: %s, overwriting", path, e
                )

        try:
            with fs.open(path, "wb") as f:
                f.write(bin_data)
        except OSError as e:
            _logger.error("Failed to write file %s: %s", path, e)
            raise

    @api.model
    def s3_enqueue_migration(
        self,
        storage_code,
        batch_size=500,
        max_batches=None,
        channel="root.s3_migration",
        max_retries=None,
    ):
        """Enqueue migration jobs using cursor pagination."""
        domain = self._s3_migration_domain(storage_code)
        total_enqueued = 0
        batches = 0
        last_id = 0

        force_db_config = self.env[
            "fs.storage"
        ].get_force_db_for_default_attachment_rules(storage_code)
        if force_db_config:
            _logger.info(
                "Migration will exclude force-DB files: %s",
                force_db_config,
            )

        _logger.info(
            "Starting migration enqueue for storage %s (batch_size=%d, max_batches=%s)",
            storage_code,
            batch_size,
            max_batches or "unlimited",
        )

        while True:
            cursor_domain = domain + [("id", ">", last_id)]
            ids = (
                self.with_context(prefetch_fields=False)
                .search(cursor_domain, limit=batch_size, order="id ASC")
                .ids
            )
            if not ids:
                break

            self.browse(ids).with_delay(
                channel=channel, max_retries=max_retries
            ).s3_migrate_batch(storage_code)

            total_enqueued += len(ids)
            batches += 1
            last_id = ids[-1]

            if batches % 10 == 0:
                _logger.info(
                    "Migration enqueue progress: %d attachments in %d batches",
                    total_enqueued,
                    batches,
                )

            if max_batches and batches >= max_batches:
                break

        _logger.info(
            "Completed migration enqueue: %d attachments in %d batches for storage %s",
            total_enqueued,
            batches,
            storage_code,
        )
        return total_enqueued

    def s3_migrate_batch(self, storage_code):
        """Migrate batch with checksum deduplication."""
        fs_storage = self.env["fs.storage"].sudo().get_by_code(storage_code)
        if not fs_storage:
            _logger.error("Storage not found: %s", storage_code)
            return False

        fs = fs_storage.fs
        optimize_path = fs_storage.optimizes_directory_path

        force_db_rules = {}
        if fs_storage.migration_use_storage_force_db_rules:
            force_db_rules = self.env[
                "fs.storage"
            ].get_force_db_for_default_attachment_rules(storage_code)

        checksum_groups = {}
        for att in self.with_context(prefetch_fields=False):
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

            if self._should_force_db(
                representative.mimetype, representative.file_size, force_db_rules
            ):
                skipped += len(attachments)
                continue

            try:
                bin_data = self._get_binary_data_for_checksum(checksum, storage_code)
            except Exception as e:  # pylint: disable=broad-except
                _logger.warning(
                    "Cannot read checksum %s: %s, skipping %d attachments",
                    checksum,
                    e,
                    len(attachments),
                )
                skipped += len(attachments)
                continue

            if not bin_data:
                _logger.warning(
                    "No data for checksum %s, skipping %d attachments",
                    checksum,
                    len(attachments),
                )
                skipped += len(attachments)
                continue

            path = self._compute_s3_path(checksum, optimize_path)

            try:
                self._upload_to_storage(fs, path, bin_data)
            except Exception as e:
                _logger.error(
                    "Upload failed for %s: %s, skipping %d attachments",
                    checksum,
                    e,
                    len(attachments),
                )
                skipped += len(attachments)
                continue

            new_store_fname = f"{storage_code}://{path}"
            fs_filename = path.split("/")[-1]

            for att in attachments:
                old_fname = att.store_fname
                if old_fname and not old_fname.startswith(f"{storage_code}://"):
                    self._mark_old_store_fname_for_gc(old_fname)
                att._force_write_store_fname(new_store_fname)

            attachments.write({"fs_filename": fs_filename})
            migrated += len(attachments)

            if migrated % 100 == 0:
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
