# Copyright 2025 Cetmix OU
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models
from odoo.osv.expression import AND, OR

_logger = logging.getLogger(__name__)

# Required tautology for ir.attachment searches to include field-linked attachments.
# Odoo's ir.attachment._search automatically adds ('res_field', '=', False) when the
# domain doesn't contain 'res_field', which would exclude all field-linked attachments.
# See: odoo/addons/base/models/ir_attachment.py _search method
RES_FIELD_DOMAIN = ["|", ("res_field", "=", False), ("res_field", "!=", False)]


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    @api.model
    def _s3_migration_domain(self, storage_code):
        """Build domain for attachments to migrate, excluding force-DB files.

        Respects force_db_for_default_attachment_rules to keep assets and
        small images in database for performance.
        """
        base = [
            ("store_fname", "not like", f"{storage_code}://%"),
        ] + RES_FIELD_DOMAIN

        force_db_domain = self._s3_get_force_db_domain(storage_code)
        if force_db_domain:
            return AND([base, ["!"] + force_db_domain])
        return base

    @api.model
    def _s3_get_force_db_domain(self, storage_code):
        """Get domain for attachments that must stay in DB for target storage.

        Returns an Odoo domain combining MIME-type prefixes and optional
        file_size limits. Each rule is normalized with AND() before OR'ing
        with the accumulated domain to ensure correct grouping.
        """
        fs_storage = self.env["fs.storage"]
        force_db_rules = fs_storage.get_force_db_for_default_attachment_rules(
            storage_code
        )
        if not force_db_rules:
            return []

        domain = None
        for mimetype_key, size_limit in force_db_rules.items():
            rule_domain = [("mimetype", "=like", f"{mimetype_key}%")]
            if size_limit:
                rule_domain = AND([rule_domain, [("file_size", "<=", size_limit)]])
            domain = OR([domain, rule_domain]) if domain else rule_domain

        return domain or []

    # ----------------------------------------------
    # Migration helpers
    # ----------------------------------------------
    def _s3_resolve_migration_bytes(self, attachment, target_storage_code):
        """Return non-empty base64 bytes for an attachment or None.

        Prefer a donor already migrated to the target storage, then a donor
        stored in DB. A donor is any attachment with the same checksum whose
        ``datas`` can be read non-empty at this moment.
        """
        checksum = attachment.checksum
        if not checksum:
            return None

        # File is already on target storage (reads from S3)
        domain_target = AND(
            [
                [
                    ("checksum", "=", checksum),
                    ("store_fname", "=like", f"{target_storage_code}://%"),
                ],
                RES_FIELD_DOMAIN,
            ]
        )
        donor = self.search(domain_target, limit=1)
        if donor:
            donor_data = donor.with_context(prefetch_fields=False).datas
            if donor_data:
                return donor_data

        # File is kept in DB (fast and independent from filestore)
        domain_db = AND(
            [[("checksum", "=", checksum), ("db_datas", "!=", False)], RES_FIELD_DOMAIN]
        )
        donor = self.search(domain_db, limit=1)
        if donor:
            donor_data = donor.with_context(prefetch_fields=False).datas
            return donor_data

        # 3) Fallback: any readable same-checksum record (avoid mass prefetch)
        domain_any = AND([[("checksum", "=", checksum)], RES_FIELD_DOMAIN])
        candidates = self.with_context(prefetch_fields=False).search(
            domain_any, limit=10
        )
        for candidate in candidates:
            donor_data = candidate.with_context(prefetch_fields=False).datas
            if donor_data:
                return donor_data
        return None

    @api.model
    def s3_enqueue_migration(
        self,
        storage_code,
        batch_size=500,
        max_batches=None,
        channel="root.s3_migration",
        max_retries=None,
    ):
        """Enqueue migration jobs for attachments using cursor pagination.

        Returns number of attachments enqueued for migration.
        """
        domain = self._s3_migration_domain(storage_code)
        total_enqueued = 0
        batches = 0
        last_id = 0

        fs_storage = self.env["fs.storage"]
        force_db_config = fs_storage.get_force_db_for_default_attachment_rules(
            storage_code
        )
        if force_db_config:
            _logger.info(
                "Migration will exclude force-DB files per storage rules: %s",
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

            rs = self.browse(ids)
            rs.with_delay(channel=channel, max_retries=max_retries).s3_migrate_batch(
                storage_code
            )

            total_enqueued += len(ids)
            batches += 1
            last_id = ids[-1]  # Move cursor to last processed ID

            # Progress logging every 10 batches
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
        """Migrate a batch of attachments to target storage."""
        rs = self.with_context(prefetch_fields=False)
        env = self.env
        total = len(rs)
        processed = 0
        skipped = 0

        _logger.info(
            "Starting batch migration: %d attachments to storage %s",
            total,
            storage_code,
        )

        for attachment in rs:
            env.clear()

            try:
                file_data = attachment.datas
                mimetype = attachment.mimetype
                name = attachment.name
            except OSError as e:
                # File missing (deleted by parallel worker) or already migrated
                _logger.debug(
                    "Skipping attachment %s (id=%s): %s",
                    attachment.name,
                    attachment.id,
                    str(e),
                )
                skipped += 1
                processed += 1
                continue

            # Avoid empty writes if source is temporarily unreadable
            if attachment.file_size and not file_data:
                resolved = self._s3_resolve_migration_bytes(attachment, storage_code)
                if not resolved:
                    _logger.warning(
                        "Skipping migration for id=%s (checksum=%s): "
                        "source bytes missing",
                        attachment.id,
                        attachment.checksum,
                    )
                    skipped += 1
                    processed += 1
                    continue
                file_data = resolved

            att = attachment.with_context(storage_location=storage_code)
            att.write({"datas": file_data, "mimetype": mimetype, "name": name})

            processed += 1
            if processed % 50 == 0 or processed % max(1, total // 10) == 0:
                _logger.info(
                    "Migration batch progress: %d/%d (%.1f%%) - storage: %s",
                    processed,
                    total,
                    (processed / total) * 100,
                    storage_code,
                )

        _logger.info(
            "Completed batch migration: %d/%d attachments to storage %s (%d skipped). "
            "Old files will be cleaned by the garbage collector.",
            processed - skipped,
            total,
            storage_code,
            skipped,
        )
        return True
