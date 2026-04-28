# Copyright 2026 APSL-Nagarro Antoni Marroig
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from .common import TestFSAttachmentS3Common


class TestFsFileGcS3(TestFSAttachmentS3Common):
    def setUp(self):
        super().setUp()
        self.gc_file_model = self.env["fs.file.gc"]

    def _mark_for_gc(self, *store_fnames):
        for store_fname in store_fnames:
            self.gc_file_model._mark_for_gc(store_fname)

    def test_gc_s3_bulk_delete_removes_orphaned_files(self):
        orphan_1 = "s3tst://dir/sub/orphan_1.txt"
        orphan_2 = "s3tst://dir/sub/orphan_2.txt"
        referenced = self.fake_attachment_s3.store_fname
        self._mark_for_gc(orphan_1, orphan_2, referenced)

        s3_client = MagicMock()
        root_fs = SimpleNamespace(s3=s3_client)

        storage_class = type(self.s3_backend)
        with (
            patch.object(
                storage_class,
                "is_s3_storage",
                new=property(lambda storage: storage.code == self.s3_backend.code),
            ),
            patch.object(storage_class, "_get_root_filesystem", return_value=root_fs),
            patch.object(type(self.env.cr), "commit", return_value=None),
        ):
            self.gc_file_model._gc_s3_bulk_delete()

        s3_client.delete_objects.assert_called_once()
        _, kwargs = s3_client.delete_objects.call_args
        self.assertEqual(kwargs["Bucket"], "test-bucket")
        self.assertCountEqual(
            kwargs["Delete"]["Objects"],
            [
                {"Key": "dir/sub/orphan_1.txt"},
                {"Key": "dir/sub/orphan_2.txt"},
            ],
        )
        remaining_files = self.gc_file_model.search(
            [("store_fname", "in", [orphan_1, orphan_2, referenced])]
        ).mapped("store_fname")
        self.assertNotIn(orphan_1, remaining_files)
        self.assertNotIn(orphan_2, remaining_files)
        self.assertIn(referenced, remaining_files)

    def test_gc_s3_bulk_delete_keeps_rows_when_s3_delete_fails(self):
        orphan = "s3tst://dir/sub/orphan.txt"
        self._mark_for_gc(orphan)

        s3_client = MagicMock()
        s3_client.delete_objects.side_effect = Exception("S3 is unavailable")
        root_fs = SimpleNamespace(s3=s3_client)

        storage_class = type(self.s3_backend)
        with (
            patch.object(
                storage_class,
                "is_s3_storage",
                new=property(lambda storage: storage.code == self.s3_backend.code),
            ),
            patch.object(storage_class, "_get_root_filesystem", return_value=root_fs),
            patch.object(type(self.env.cr), "commit", return_value=None),
        ):
            self.gc_file_model._gc_s3_bulk_delete()

        self.assertTrue(self.gc_file_model.search_count([("store_fname", "=", orphan)]))
