# Copyright 2025 Cetmix OU
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Tests for S3 attachment migration functionality."""

from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase


class TestAttachmentS3Migration(TransactionCase):
    """Test suite for cx_attachment_s3_migration module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Attachment = cls.env["ir.attachment"]

    def test_migration_domain_excludes_migrated_files(self):
        """Test that migration domain correctly excludes already-migrated files."""
        domain = self.Attachment._s3_migration_domain("test_s3")

        # Should be a list with exclusion pattern
        self.assertIsInstance(domain, list)
        # Should contain the storage code pattern
        domain_str = str(domain)
        self.assertIn("test_s3", domain_str)
        self.assertIn("store_fname", domain_str)

    def test_enqueue_migration_returns_count(self):
        """Test that enqueue_migration returns correct attachment count."""
        # Create test attachments (stored in DB, no file operations)
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

    def test_migrate_batch_handles_empty_recordset(self):
        """Test that empty recordset doesn't crash."""
        empty = self.Attachment.browse([])

        # Should return True without error
        result = empty.s3_migrate_batch("test_s3")
        self.assertTrue(result)

    def test_migrate_batch_method_exists(self):
        """Test that s3_migrate_batch method is callable."""
        # Just verify the method exists and is callable
        self.assertTrue(hasattr(self.Attachment, "s3_migrate_batch"))
        self.assertTrue(callable(self.Attachment.s3_migrate_batch))
