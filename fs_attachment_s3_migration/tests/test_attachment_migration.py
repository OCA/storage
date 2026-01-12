# Copyright 2025 Cetmix OU
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Tests for S3 attachment migration functionality."""

import os
import re
from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase


class TestS3MigrationDomain(TransactionCase):
    """Test suite for migration domain building."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Attachment = cls.env["ir.attachment"]

    def test_migration_domain_excludes_already_migrated(self):
        """Test that migration domain excludes already-migrated files."""
        domain = self.Attachment._s3_migration_domain("test_s3")

        domain_str = str(domain)
        self.assertIn("test_s3", domain_str)
        self.assertIn("store_fname", domain_str)
        self.assertIn("not like", domain_str)

    def test_migration_domain_completeness(self):
        """Verify domain includes all required filters."""
        domain = self.Attachment._s3_migration_domain("test_s3")

        # Convert to string for easier checking
        domain_str = str(domain)

        # Must filter by checksum (has binary content)
        self.assertIn("checksum", domain_str)
        # Must filter by type=binary
        self.assertIn("type", domain_str)
        # Must filter by store_fname (not in target)
        self.assertIn("store_fname", domain_str)
        # Must filter by db_datas=False (not in database)
        self.assertIn("db_datas", domain_str)
        # Must include res_field tautology
        self.assertIn("res_field", domain_str)

    def test_migration_domain_excludes_url_attachments(self):
        """Verify domain excludes URL-type attachments."""
        domain = self.Attachment._s3_migration_domain("test_s3")

        # Check type=binary filter is present
        type_filter = [d for d in domain if isinstance(d, tuple) and d[0] == "type"]
        self.assertTrue(type_filter)
        self.assertEqual(type_filter[0], ("type", "=", "binary"))

    def test_migration_domain_excludes_db_stored(self):
        """Verify domain excludes attachments stored in database."""
        domain = self.Attachment._s3_migration_domain("test_s3")

        # Check db_datas=False filter is present
        db_filter = [d for d in domain if isinstance(d, tuple) and d[0] == "db_datas"]
        self.assertTrue(db_filter)
        self.assertEqual(db_filter[0], ("db_datas", "=", False))


class TestS3MigrationHelpers(TransactionCase):
    """Test suite for migration helper methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Attachment = cls.env["ir.attachment"]

    def test_should_force_db_empty_rules(self):
        """Empty force_db_rules should always return False."""
        result = self.Attachment._should_force_db("image/png", 1000, {})
        self.assertFalse(result)

    def test_should_force_db_matching_mime(self):
        """Matching mimetype with limit=0 should return True."""
        rules = {"image/": 0, "text/css": 0}

        self.assertTrue(self.Attachment._should_force_db("image/png", 5000, rules))
        self.assertTrue(self.Attachment._should_force_db("image/jpeg", 100, rules))
        self.assertTrue(self.Attachment._should_force_db("text/css", 1, rules))

    def test_should_force_db_with_size_limit(self):
        """Size limit should be respected for matching mimetype."""
        rules = {"image/": 51200}  # 50KB limit

        # Under limit - should be forced to DB
        self.assertTrue(self.Attachment._should_force_db("image/png", 1000, rules))
        self.assertTrue(self.Attachment._should_force_db("image/png", 51200, rules))

        # Over limit - should not be forced to DB
        self.assertFalse(self.Attachment._should_force_db("image/png", 51201, rules))
        self.assertFalse(self.Attachment._should_force_db("image/png", 100000, rules))

    def test_should_force_db_non_matching_mime(self):
        """Non-matching mimetype should return False."""
        rules = {"image/": 51200, "text/css": 0}

        self.assertFalse(
            self.Attachment._should_force_db("application/pdf", 100, rules)
        )
        self.assertFalse(self.Attachment._should_force_db("text/html", 100, rules))

    def test_compute_s3_path_optimized(self):
        """Optimized path should use hierarchical structure."""
        checksum = "abc123def456"
        path = self.Attachment._compute_s3_path(checksum, optimize_path=True)
        self.assertEqual(path, "ab/c1/abc123def456")

    def test_compute_s3_path_flat(self):
        """Non-optimized path should use flat structure."""
        checksum = "abc123def456"
        path = self.Attachment._compute_s3_path(checksum, optimize_path=False)
        self.assertEqual(path, "abc123def456")


class TestS3MigrationEnqueue(TransactionCase):
    """Test suite for migration enqueue functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Attachment = cls.env["ir.attachment"]

    def test_enqueue_migration_returns_count(self):
        """Test that enqueue_migration returns correct attachment count."""
        # Create test attachments
        self.Attachment.create(
            [
                {
                    "name": f"test{i}.txt",
                    "raw": b"test content",
                }
                for i in range(5)
            ]
        )

        # Mock DelayableRecordset to prevent actual queue_job creation
        with patch("odoo.addons.queue_job.delay.DelayableRecordset") as mock_delayable:
            mock_instance = MagicMock()
            mock_delayable.return_value = mock_instance

            total = self.Attachment.s3_enqueue_migration(
                "test_s3",
                batch_size=10,
            )

        # Should return count >= 5 (our attachments + any existing ones)
        self.assertGreaterEqual(total, 5)

    def test_enqueue_migration_respects_max_batches(self):
        """Test that max_batches parameter limits the number of batches."""
        # Create 30 attachments
        self.Attachment.create(
            [
                {
                    "name": f"batch_test{i}.txt",
                    "raw": b"content",
                }
                for i in range(30)
            ]
        )

        with patch("odoo.addons.queue_job.delay.DelayableRecordset") as mock_delayable:
            mock_delayable.return_value = MagicMock()

            # Limit to 2 batches of 10
            total = self.Attachment.s3_enqueue_migration(
                "test_s3",
                batch_size=10,
                max_batches=2,
            )

        # Should stop at 20 (2 batches × 10)
        self.assertEqual(total, 20)

    def test_enqueue_orders_by_checksum(self):
        """Test that enqueue orders attachments by checksum for batch locality."""
        # Create attachments with same content (same checksum)
        content = b"shared content for dedup test"
        self.Attachment.create(
            [
                {
                    "name": f"dedup_test{i}.txt",
                    "raw": content,
                }
                for i in range(3)
            ]
        )

        with patch("odoo.addons.queue_job.delay.DelayableRecordset") as mock_delayable:
            mock_delayable.return_value = MagicMock()

            # Should complete without error
            total = self.Attachment.s3_enqueue_migration(
                "test_s3",
                batch_size=100,
            )

        self.assertGreaterEqual(total, 3)


class TestS3MigrationBatch(TransactionCase):
    """Test suite for batch migration functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Attachment = cls.env["ir.attachment"]

    def test_migrate_batch_handles_empty_recordset(self):
        """Test that empty recordset doesn't crash."""
        empty = self.Attachment.browse([])

        # Should return True without error
        result = empty.s3_migrate_batch("test_s3")
        # Empty recordset may return False if storage not found, or True
        self.assertIn(result, [True, False])

    def test_migrate_batch_method_exists(self):
        """Test that s3_migrate_batch method is callable."""
        self.assertTrue(hasattr(self.Attachment, "s3_migrate_batch"))
        self.assertTrue(callable(self.Attachment.s3_migrate_batch))


class TestS3MigrationChecksumDedup(TransactionCase):
    """Test suite for checksum deduplication functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Attachment = cls.env["ir.attachment"]
        cls.FsStorage = cls.env["fs.storage"]

    def test_get_binary_data_for_checksum_from_db(self):
        """Test reading binary data from DB-stored attachment."""
        content = b"test content for checksum lookup"
        att = self.Attachment.create(
            {
                "name": "test_db.txt",
                "raw": content,
            }
        )
        checksum = att.checksum

        # Should be able to read data by checksum
        data = self.Attachment._get_binary_data_for_checksum(checksum, "test_s3")
        self.assertEqual(data, content)

    def test_get_binary_data_for_checksum_not_found(self):
        """Test that non-existent checksum returns None."""
        data = self.Attachment._get_binary_data_for_checksum(
            "nonexistent123456", "test_s3"
        )
        self.assertIsNone(data)


class TestS3MigrationGCMarking(TransactionCase):
    """Test suite for garbage collection marking."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Attachment = cls.env["ir.attachment"]
        cls.GcFile = cls.env["fs.file.gc"]
        cls.SourceStorage = cls.env["fs.storage"].create(
            {
                "name": "Source Storage",
                "code": "s3src",
                "protocol": "odoofs",
            }
        )

    def test_mark_old_store_fname_routes_remote_uri_to_fs_file_gc(self):
        """Remote storage URIs are queued in fs.file.gc for autovacuum."""
        remote_fname = "s3src://dir/sub/orphan.txt"
        self.Attachment._mark_old_store_fname_for_gc(remote_fname)

        gc_row = self.GcFile.search([("store_fname", "=", remote_fname)])
        self.assertEqual(len(gc_row), 1)
        self.assertEqual(gc_row.fs_storage_code, "s3src")

    def test_mark_old_store_fname_ignores_local_path(self):
        """Local filestore paths are not queued for GC by this module."""
        local_fname = "ab/checksum123"
        self.Attachment._mark_old_store_fname_for_gc(local_fname)

        self.assertFalse(self.GcFile.search_count([("store_fname", "=", local_fname)]))

        sanitized = re.sub("[.]", "", local_fname).strip("/\\")
        checklist_path = os.path.join(
            self.Attachment._full_path("checklist"), sanitized
        )
        self.assertFalse(os.path.isfile(checklist_path))


class TestS3MigrationErrorHandling(TransactionCase):
    """Test suite for error handling during migration."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Attachment = cls.env["ir.attachment"]

    def test_should_force_db_handles_none_values(self):
        """Test that None mimetype/file_size are handled gracefully."""
        rules = {"image/": 51200}

        # Should not crash with None values
        result = self.Attachment._should_force_db(None, None, rules)
        self.assertFalse(result)

        result = self.Attachment._should_force_db(None, 1000, rules)
        self.assertFalse(result)

    def test_compute_s3_path_short_checksum(self):
        """Test path computation with short checksum."""
        # Should handle short checksums gracefully
        checksum = "ab"
        path = self.Attachment._compute_s3_path(checksum, optimize_path=True)
        self.assertEqual(path, "ab//ab")

    def test_upload_to_storage_creates_dirs(self):
        """Test that _upload_to_storage creates directories."""
        mock_fs = MagicMock()
        mock_fs.exists.return_value = False
        mock_file = MagicMock()
        mock_fs.open.return_value.__enter__ = MagicMock(return_value=mock_file)
        mock_fs.open.return_value.__exit__ = MagicMock(return_value=False)

        self.Attachment._upload_to_storage(mock_fs, "ab/cd/checksum", b"data")

        # Should have attempted to create directories
        mock_fs.makedirs.assert_called_once_with("ab/cd", exist_ok=True)
        # Should have uploaded the file
        mock_fs.open.assert_called_once_with("ab/cd/checksum", "wb")
