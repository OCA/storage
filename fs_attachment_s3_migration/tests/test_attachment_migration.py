# Copyright 2026 Cetmix OU
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Tests for S3 attachment migration functionality."""

import os
import re
import shutil
import tempfile
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.osv.expression import AND
from odoo.tools import mute_logger

from odoo.addons.base.tests.common import BaseCommon
from odoo.addons.queue_job.tests.common import trap_jobs


class S3MigrationCommon(BaseCommon):
    """Shared helpers for migration tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Attachment = cls.env["ir.attachment"]
        cls.FsStorage = cls.env["fs.storage"]
        cls.Wizard = cls.env["s3.migration.wizard"]

    @contextmanager
    def _restrict_migration_domain(self, attachments):
        """Limit enqueue selection to ``attachments`` (ignore other test data)."""
        origin = self.Attachment._s3_migration_domain

        def _restricted(storage_code):
            return AND([origin(storage_code), [("id", "in", attachments.ids)]])

        with patch.object(
            type(self.Attachment),
            "_s3_migration_domain",
            side_effect=_restricted,
        ):
            yield


class TestS3MigrationDomain(S3MigrationCommon):
    """Test suite for migration domain building."""

    def test_migration_domain_excludes_already_migrated(self):
        domain = self.Attachment._s3_migration_domain("test_s3")
        store_filters = [
            d for d in domain if isinstance(d, tuple) and d[0] == "store_fname"
        ]
        self.assertIn(("store_fname", "not like", "test_s3://%"), store_filters)

    def test_migration_domain_completeness(self):
        domain = self.Attachment._s3_migration_domain("test_s3")
        fields_used = {d[0] for d in domain if isinstance(d, tuple)}
        self.assertTrue({"checksum", "type", "store_fname", "db_datas"} <= fields_used)

    def test_migration_domain_excludes_url_attachments(self):
        domain = self.Attachment._s3_migration_domain("test_s3")
        type_filter = [d for d in domain if isinstance(d, tuple) and d[0] == "type"]
        self.assertEqual(type_filter[0], ("type", "=", "binary"))

    def test_migration_domain_excludes_db_stored(self):
        """DB-stored attachments are not migrated (donors only)."""
        domain = self.Attachment._s3_migration_domain("test_s3")
        db_filter = [d for d in domain if isinstance(d, tuple) and d[0] == "db_datas"]
        self.assertEqual(db_filter[0], ("db_datas", "=", False))


class TestS3MigrationForceDbDomain(S3MigrationCommon):
    """Force-DB domain delegates to the core helper."""

    def test_s3_get_force_db_domain_reuses_core_rules(self):
        rules = {"image/": 51200, "text/css": 0}
        with patch.object(
            type(self.FsStorage),
            "get_force_db_for_default_attachment_rules",
            return_value=rules,
        ):
            domain = self.Attachment._s3_get_force_db_domain("unused")

        domain_str = str(domain)
        self.assertIn("image/", domain_str)
        self.assertIn("text/css", domain_str)
        self.assertIn("file_size", domain_str)

    def test_s3_get_force_db_domain_empty_rules(self):
        with patch.object(
            type(self.FsStorage),
            "get_force_db_for_default_attachment_rules",
            return_value={},
        ):
            domain = self.Attachment._s3_get_force_db_domain("unused")
        self.assertEqual(domain, [])


class TestS3MigrationPacking(S3MigrationCommon):
    """Checksum-aware batch packing never splits a group."""

    def test_pack_keeps_checksum_groups_together(self):
        rows = [
            {"id": 1, "checksum": "aaa"},
            {"id": 2, "checksum": "aaa"},
            {"id": 3, "checksum": "bbb"},
            {"id": 4, "checksum": "ccc"},
            {"id": 5, "checksum": "ccc"},
            {"id": 6, "checksum": "ccc"},
        ]
        batches = self.Attachment._s3_pack_checksum_batches(rows, batch_size=3)
        self.assertEqual(batches, [[1, 2, 3], [4, 5, 6]])

    def test_pack_oversized_checksum_group_stays_in_one_batch(self):
        rows = [{"id": i, "checksum": "aaa"} for i in range(5)]
        batches = self.Attachment._s3_pack_checksum_batches(rows, batch_size=3)
        self.assertEqual(batches, [[0, 1, 2, 3, 4]])


class TestS3MigrationEnqueue(S3MigrationCommon):
    """Enqueue uses trap_jobs and exact fixture membership."""

    def _create_unique_attachments(self, count, prefix, content_fn=None):
        vals = []
        for i in range(count):
            content = content_fn(i) if content_fn else f"{prefix}-{i}".encode()
            vals.append({"name": f"{prefix}_{i}.txt", "raw": content})
        return self.Attachment.create(vals)

    def test_enqueue_migration_returns_exact_count(self):
        atts = self._create_unique_attachments(5, "enq_exact")
        with self._restrict_migration_domain(atts), trap_jobs() as trap:
            total = self.Attachment._s3_enqueue_migration(
                "test_s3",
                batch_size=10,
            )
        self.assertEqual(total, 5)
        self.assertEqual(len(trap.enqueued_jobs), 1)
        self.assertEqual(trap.enqueued_jobs[0].func.__name__, "s3_migrate_batch")
        self.assertEqual(set(trap.enqueued_jobs[0].recordset.ids), set(atts.ids))

    def test_enqueue_migration_respects_max_batches(self):
        atts = self._create_unique_attachments(6, "enq_maxb")
        with self._restrict_migration_domain(atts), trap_jobs() as trap:
            total = self.Attachment._s3_enqueue_migration(
                "test_s3",
                batch_size=2,
                max_batches=2,
            )
        self.assertEqual(total, 4)
        self.assertEqual(len(trap.enqueued_jobs), 2)
        enqueued_ids = {i for job in trap.enqueued_jobs for i in job.recordset.ids}
        self.assertEqual(len(enqueued_ids), 4)
        self.assertTrue(enqueued_ids.issubset(set(atts.ids)))

    def test_enqueue_does_not_split_checksum_groups(self):
        shared = b"shared content for checksum locality"
        same = self.Attachment.create(
            [{"name": f"dedup_{i}.txt", "raw": shared} for i in range(3)]
        )
        others = self._create_unique_attachments(2, "dedup_other")
        atts = same | others
        with self._restrict_migration_domain(atts), trap_jobs() as trap:
            total = self.Attachment._s3_enqueue_migration(
                "test_s3",
                batch_size=3,
            )
        self.assertEqual(total, 5)
        checksums_seen = []
        for job in trap.enqueued_jobs:
            checksums = set(job.recordset.mapped("checksum"))
            checksums_seen.extend(checksums)
            same_ids = set(same.ids) & set(job.recordset.ids)
            if same_ids:
                self.assertEqual(same_ids, set(same.ids))
        self.assertEqual(len(checksums_seen), len(set(checksums_seen)))

    def test_enqueue_sets_identity_key_and_channel(self):
        atts = self._create_unique_attachments(2, "enq_ident")
        with self._restrict_migration_domain(atts), trap_jobs() as trap:
            self.Attachment._s3_enqueue_migration(
                "ident_s3",
                batch_size=10,
                channel="root.s3_migration",
            )
        job = trap.enqueued_jobs[0]
        self.assertTrue(job.identity_key.startswith("s3-migration-ident_s3-"))
        self.assertEqual(job.channel, "root.s3_migration")

    def test_enqueue_refuses_non_admin(self):
        user = self.env["res.users"].create(
            {
                "name": "S3 Mig Internal",
                "login": "s3_mig_internal",
                "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
            }
        )
        with self.assertRaises(AccessError):
            self.Attachment.with_user(user)._s3_enqueue_migration("test_s3")

    def test_enqueue_refuses_overlapping_run(self):
        with patch.object(
            type(self.Attachment),
            "_s3_has_pending_migration_jobs",
            return_value=True,
        ), self.assertRaises(UserError):
            self.Attachment._s3_enqueue_migration("test_s3")


class TestS3MigrationBatch(S3MigrationCommon):
    """Batch migration against a local file storage backend."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.temp_dir = tempfile.mkdtemp()
        cls.addClassCleanup(lambda: shutil.rmtree(cls.temp_dir, ignore_errors=True))
        cls.storage = cls.FsStorage.create(
            {
                "name": "Migration File Storage",
                "code": "migfile",
                "protocol": "file",
                "directory_path": cls.temp_dir,
                "use_filename_obfuscation": True,
                "optimizes_directory_path": True,
            }
        )
        cls.FsStorage.clear_caches()

    def test_migrate_batch_handles_empty_recordset(self):
        empty = self.Attachment.browse([])
        self.assertTrue(empty.s3_migrate_batch("missing_storage"))
        self.assertTrue(empty.s3_migrate_batch(self.storage.code))

    def test_migrate_batch_repoints_store_fname(self):
        content = b"migrate-me-unique-payload"
        att = self.Attachment.create({"name": "to_mig.txt", "raw": content})
        old_fname = att.store_fname
        self.assertTrue(old_fname)
        self.assertFalse(old_fname.startswith(f"{self.storage.code}://"))

        self.assertTrue(att.s3_migrate_batch(self.storage.code))
        att.invalidate_recordset()
        self.assertTrue(att.store_fname.startswith(f"{self.storage.code}://"))
        self.assertNotEqual(att.store_fname, old_fname)

    def test_migrate_batch_missing_storage_returns_false(self):
        att = self.Attachment.create({"name": "no_store.txt", "raw": b"x"})
        with mute_logger("odoo.addons.fs_attachment_s3_migration.models.ir_attachment"):
            self.assertFalse(att.s3_migrate_batch("does_not_exist"))

    def test_migrate_batch_propagates_upload_errors(self):
        att = self.Attachment.create({"name": "fail_up.txt", "raw": b"payload"})
        with patch.object(
            type(self.Attachment),
            "_upload_to_storage",
            side_effect=OSError("S3 unavailable"),
        ), self.assertRaises(OSError):
            att.s3_migrate_batch(self.storage.code)

    def test_migrate_batch_skips_when_row_lock_unavailable(self):
        att = self.Attachment.create({"name": "locked.txt", "raw": b"locked-payload"})
        old_fname = att.store_fname
        with patch.object(
            type(att),
            "_s3_lock_attachment_or_skip",
            return_value=False,
        ):
            self.assertTrue(att.s3_migrate_batch(self.storage.code))
        att.invalidate_recordset()
        self.assertEqual(att.store_fname, old_fname)


class TestS3MigrationChecksumDedup(S3MigrationCommon):
    """Checksum lookup helpers."""

    def test_get_binary_data_for_checksum_from_db(self):
        content = b"test content for checksum lookup"
        att = self.Attachment.create({"name": "test_db.txt", "raw": content})
        data = self.Attachment._get_binary_data_for_checksum(att.checksum, "test_s3")
        self.assertEqual(data, content)

    def test_get_binary_data_for_checksum_not_found(self):
        data = self.Attachment._get_binary_data_for_checksum(
            "nonexistent123456", "test_s3"
        )
        self.assertIsNone(data)

    def test_get_binary_data_for_checksum_keeps_empty_bytes(self):
        att = self.Attachment.create({"name": "empty.bin", "raw": b""})
        data = self.Attachment._get_binary_data_for_checksum(att.checksum, "test_s3")
        self.assertEqual(data, b"")


class TestS3MigrationGCMarking(S3MigrationCommon):
    """Garbage collection marking."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.GcFile = cls.env["fs.file.gc"]
        cls.SourceStorage = cls.FsStorage.create(
            {
                "name": "Source Storage",
                "code": "s3src",
                "protocol": "odoofs",
            }
        )
        cls.FsStorage.clear_caches()

    def test_mark_old_store_fname_routes_remote_uri_to_fs_file_gc(self):
        remote_fname = "s3src://dir/sub/orphan.txt"
        self.Attachment._mark_old_store_fname_for_gc(remote_fname)
        gc_row = self.GcFile.search([("store_fname", "=", remote_fname)])
        self.assertEqual(len(gc_row), 1)
        self.assertEqual(gc_row.fs_storage_code, "s3src")

    def test_mark_old_store_fname_ignores_local_path(self):
        local_fname = "ab/checksum123"
        self.Attachment._mark_old_store_fname_for_gc(local_fname)
        self.assertFalse(self.GcFile.search_count([("store_fname", "=", local_fname)]))
        sanitized = re.sub("[.]", "", local_fname).strip("/\\")
        checklist_path = os.path.join(
            self.Attachment._full_path("checklist"), sanitized
        )
        self.assertFalse(os.path.isfile(checklist_path))


class TestS3MigrationUpload(S3MigrationCommon):
    """Size-check shortcut around the core write path."""

    def test_upload_skips_write_when_size_matches(self):
        mock_fs = MagicMock()
        mock_fs.exists.return_value = True
        mock_fs.info.return_value = {"size": 4}
        with patch.object(
            type(self.Attachment),
            "_get_fs_storage_for_code",
            return_value=mock_fs,
        ), patch.object(
            type(self.Attachment),
            "_get_fs_path",
            return_value="ab/cd/checksum",
        ), patch.object(
            type(self.Attachment),
            "_storage_file_write",
        ) as mock_write:
            fname = self.Attachment._upload_to_storage("test_s3", b"data")
        mock_write.assert_not_called()
        self.assertEqual(fname, "test_s3://ab/cd/checksum")

    def test_upload_delegates_to_core_write_when_missing(self):
        mock_fs = MagicMock()
        mock_fs.exists.return_value = False
        with patch.object(
            type(self.Attachment),
            "_get_fs_storage_for_code",
            return_value=mock_fs,
        ), patch.object(
            type(self.Attachment),
            "_get_fs_path",
            return_value="ab/cd/checksum",
        ), patch.object(
            type(self.Attachment),
            "_storage_file_write",
            return_value="test_s3://ab/cd/checksum",
        ) as mock_write:
            fname = self.Attachment._upload_to_storage(
                "test_s3", b"data", mimetype="text/plain"
            )
        mock_write.assert_called_once_with(b"data")
        self.assertEqual(fname, "test_s3://ab/cd/checksum")


class TestS3MigrationWizard(S3MigrationCommon):
    """Wizard derives storage_code from storage_id and validates inputs."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.s3_storage = cls.FsStorage.create(
            {
                "name": "S3 Wizard Storage",
                "protocol": "s3",
                "code": "s3wiz",
                "directory_path": "test-bucket",
                "json_options": {
                    "key": "aws-key",
                    "secret": "aws-secret",
                    "client_kwargs": {
                        "endpoint_url": "http://minio.minio/",
                        "region_name": "aws-region",
                    },
                },
            }
        )
        cls.file_storage = cls.FsStorage.create(
            {
                "name": "File Wizard Storage",
                "protocol": "file",
                "code": "filewiz",
                "directory_path": "/tmp",
            }
        )
        cls.FsStorage.clear_caches()

    def test_storage_code_follows_storage_id(self):
        wizard = self.Wizard.create({"storage_id": self.s3_storage.id})
        self.assertEqual(wizard.storage_code, "s3wiz")
        self.assertTrue(wizard.channel_id)
        self.assertEqual(wizard.channel_id.complete_name, "root.s3_migration")

    def test_confirm_rejects_non_s3_storage(self):
        wizard = self.Wizard.create({"storage_id": self.file_storage.id})
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_batch_size_must_be_positive(self):
        wizard = self.Wizard.create({"storage_id": self.s3_storage.id})
        with self.assertRaises(ValidationError):
            wizard.batch_size = 0

    def test_max_batches_must_not_be_negative(self):
        wizard = self.Wizard.create({"storage_id": self.s3_storage.id})
        with self.assertRaises(ValidationError):
            wizard.max_batches = -1

    def test_open_wizard_rejects_non_s3(self):
        with self.assertRaises(UserError):
            self.file_storage.action_open_migration_wizard()

    def test_confirm_enqueues_using_storage_id_code(self):
        atts = self.Attachment.create(
            [{"name": f"wiz_{i}.txt", "raw": f"wiz-{i}".encode()} for i in range(2)]
        )
        wizard = self.Wizard.create(
            {"storage_id": self.s3_storage.id, "batch_size": 10}
        )
        with self._restrict_migration_domain(atts), trap_jobs() as trap:
            result = wizard.action_confirm()
        self.assertEqual(result["params"]["type"], "success")
        self.assertEqual(len(trap.enqueued_jobs), 1)
        self.assertEqual(trap.enqueued_jobs[0].func.__name__, "s3_migrate_batch")
        self.assertEqual(trap.enqueued_jobs[0].args, ("s3wiz",))
