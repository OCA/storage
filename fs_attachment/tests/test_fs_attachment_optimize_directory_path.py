# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import hashlib
import os
from unittest import mock

from ..models.ir_attachment import is_checksum_format
from .common import MyException, TestFSAttachmentCommon


class TestFSAttachmentOptimizeDirectoryPath(TestFSAttachmentCommon):
    def _create_root_attachment(self, content, name="test.txt"):
        attachment = (
            self.env["ir.attachment"]
            .with_context(storage_location=self.temp_backend.code)
            .create({"name": name, "raw": content})
        )
        self.assertNotIn("/", attachment.store_fname.partition("://")[2])
        return attachment

    def _optimized_store_fname(self, attachment, path):
        checksum = attachment.checksum
        return f"tmp_dir://{checksum[:2]}/{checksum[2:4]}/{path}"

    def _gc_marked(self, store_fname):
        return self.gc_file_model.search_count([("store_fname", "=", store_fname)])

    def test_shared_file_moves_all_attachments(self):
        self.temp_backend.use_filename_obfuscation = True
        content = b"shared content"
        attachment_1 = self._create_root_attachment(content)
        attachment_2 = self._create_root_attachment(content)
        store_fname = attachment_1.store_fname
        self.assertEqual(attachment_2.store_fname, store_fname)
        old_path = store_fname.partition("://")[2]

        self.temp_backend.optimizes_directory_path = True
        # limit=1 selects one attachment, but its file is shared by both
        self.env["ir.attachment"]._cron_fs_optimize_directory_path(limit=1)
        self.gc_file_model._gc_files_unsafe()

        target = self._optimized_store_fname(attachment_1, old_path)
        self.assertEqual(attachment_1.store_fname, target)
        self.assertEqual(attachment_2.store_fname, target)
        self.assertEqual(attachment_1.raw, content)
        self.assertEqual(attachment_2.raw, content)
        self.assertFalse(os.path.exists(os.path.join(self.temp_dir, old_path)))

    def test_copy_failure_changes_nothing(self):
        content = b"content to move"
        attachment = self._create_root_attachment(content)
        store_fname = attachment.store_fname
        old_path = store_fname.partition("://")[2]

        # the file is already marked when it is written: only a new mark counts
        gc_marked = self._gc_marked(store_fname)
        self.temp_backend.optimizes_directory_path = True
        fs = self.env["fs.storage"].get_fs_by_code(self.temp_backend.code)
        with (
            mock.patch.object(type(fs), "copy", side_effect=MyException),
            self.assertRaises(MyException),
            self.env.cr.savepoint(),
        ):
            self.env["ir.attachment"]._cron_fs_optimize_directory_path()
        attachment.invalidate_recordset()

        self.assertEqual(attachment.store_fname, store_fname)
        self.assertEqual(attachment.raw, content)
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, old_path)))
        self.assertEqual(self._gc_marked(store_fname), gc_marked)

    def test_move_file_standalone_twice(self):
        content = b"standalone move"
        attachment = self._create_root_attachment(content)
        store_fname = attachment.store_fname
        old_path = store_fname.partition("://")[2]
        target = self._optimized_store_fname(attachment, old_path)
        fs_storage_model = self.env["fs.storage"]

        moved = fs_storage_model._fs_move_file(store_fname, target)
        self.assertEqual(moved, attachment)
        self.assertEqual(attachment.store_fname, target)
        self.assertTrue(self._gc_marked(store_fname))

        # no attachment uses the source anymore: nothing is done
        moved = fs_storage_model._fs_move_file(store_fname, target)
        self.assertFalse(moved)
        self.assertEqual(attachment.store_fname, target)
        self.assertEqual(attachment.raw, content)

    def test_move_file_target_exists(self):
        content = b"target already there"
        attachment = self._create_root_attachment(content)
        store_fname = attachment.store_fname
        old_path = store_fname.partition("://")[2]
        target = self._optimized_store_fname(attachment, old_path)
        target_path = os.path.join(self.temp_dir, target.partition("://")[2])
        os.makedirs(os.path.dirname(target_path))
        with open(target_path, "wb") as f:
            f.write(content)

        fs = self.env["fs.storage"].get_fs_by_code(self.temp_backend.code)
        with mock.patch.object(type(fs), "copy") as copy:
            self.env["fs.storage"]._fs_move_file(store_fname, target)
        copy.assert_not_called()
        self.assertEqual(attachment.store_fname, target)
        self.assertEqual(attachment.raw, content)

    def test_cron_deactivates_when_done(self):
        self._create_root_attachment(b"first file", name="first.txt")
        self._create_root_attachment(b"second file", name="second.txt")
        self.temp_backend.optimizes_directory_path = True
        cron = self.env.ref("fs_attachment.ir_cron_fs_optimize_directory_path")
        attachment_model = self.env["ir.attachment"]

        progress = self.env["ir.cron.progress"].create({"cron_id": cron.id})
        attachment_model.with_context(
            ir_cron_progress_id=progress.id
        )._cron_fs_optimize_directory_path(limit=1)
        self.assertEqual(progress.done, 1)
        self.assertEqual(progress.remaining, 1)
        self.assertFalse(progress.deactivate)

        progress = self.env["ir.cron.progress"].create({"cron_id": cron.id})
        attachment_model.with_context(
            ir_cron_progress_id=progress.id
        )._cron_fs_optimize_directory_path(limit=1)
        self.assertEqual(progress.done, 1)
        self.assertEqual(progress.remaining, 0)
        self.assertTrue(progress.deactivate)

    def test_is_checksum_format(self):
        checksum = hashlib.sha1(b"content").hexdigest()
        self.assertTrue(is_checksum_format(checksum))
        self.assertFalse(is_checksum_format(checksum.upper()))
        self.assertFalse(is_checksum_format(checksum[:-1]))
        self.assertFalse(is_checksum_format("test-1-0.txt"))
        self.assertFalse(is_checksum_format(None))

    def _clear_checksum(self, attachment):
        self.env.cr.execute(
            "UPDATE ir_attachment SET checksum = NULL WHERE id = %s",
            (attachment.id,),
        )
        attachment.invalidate_recordset(["checksum"])

    def test_optimized_path_without_checksum_uses_checksum_filename(self):
        self.temp_backend.use_filename_obfuscation = True
        attachment = self._create_root_attachment(b"obfuscated")
        filename = attachment.store_fname.partition("://")[2]
        self._clear_checksum(attachment)

        self.assertEqual(
            attachment._get_optimized_path(),
            f"{filename[:2]}/{filename[2:4]}/{filename}",
        )

    def test_optimized_path_without_checksum_hashes_filename(self):
        attachment = self._create_root_attachment(b"readable name")
        filename = attachment.store_fname.partition("://")[2]
        self.assertFalse(is_checksum_format(filename))
        self._clear_checksum(attachment)

        key = hashlib.sha1(filename.encode()).hexdigest()
        self.assertEqual(
            attachment._get_optimized_path(),
            f"{key[:2]}/{key[2:4]}/{filename}",
        )

    def test_optimize_directory_path_of_existing_files(self):
        content = b"This is a test attachment"
        attachment = (
            self.env["ir.attachment"]
            .with_context(storage_location=self.temp_backend.code)
            .create({"name": "test.txt", "raw": content})
        )
        old_path = attachment.store_fname.partition("://")[2]
        self.assertNotIn("/", old_path)

        self.temp_backend.optimizes_directory_path = True
        self.env["ir.attachment"]._cron_fs_optimize_directory_path()
        self.gc_file_model._gc_files_unsafe()

        checksum = attachment.checksum
        self.assertEqual(
            attachment.store_fname,
            f"tmp_dir://{checksum[:2]}/{checksum[2:4]}/{old_path}",
        )
        self.assertEqual(attachment.raw, content)
        self.assertFalse(os.path.exists(os.path.join(self.temp_dir, old_path)))
        self.assertEqual(
            self.env["ir.attachment"].search_count(
                [("store_fname", "=", f"tmp_dir://{old_path}")]
            ),
            0,
        )
