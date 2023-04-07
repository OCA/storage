# Copyright 2023 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import os
import shutil
import tempfile

from odoo.tests.common import TransactionCase


class TestFSAttachment(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.backend = cls.env.ref("fs_storage.default_fs_storage")
        temp_dir = tempfile.mkdtemp()
        cls.temp_backend = cls.env["fs.storage"].create(
            {
                "name": "Temp FS Storage",
                "protocol": "file",
                "code": "tmp_dir",
                "directory_path": temp_dir,
            }
        )
        cls.temp_dir = temp_dir

        @cls.addClassCleanup
        def cleanup_tempdir():
            shutil.rmtree(temp_dir)

    def test_create_attachment_explicit_location(self):
        content = b"This is a test attachment"
        attachment = (
            self.env["ir.attachment"]
            .with_context(
                storage_location=self.temp_backend.code,
                storage_file_path="test.txt",
            )
            .create({"name": "Test Attachment", "raw": content})
        )
        self.env.flush_all()
        self.assertEqual(os.listdir(self.temp_dir), ["test.txt"])
        self.assertEqual(attachment.raw, content)
        self.assertFalse(attachment.db_datas)
        with attachment.open("rb") as f:
            self.assertEqual(f.read(), content)

        with attachment.open("wb") as f:
            f.write(b"new")
        # refresh is required while we don't use a file-like object proxy
        # that detect the modification of the content and invalidate the
        # record's cache
        attachment.refresh()
        self.assertEqual(attachment.raw, b"new")

    def test_open_attachment_in_db(self):
        self.env["ir.config_parameter"].sudo().set_param("ir_attachment.location", "db")
        content = b"This is a test attachment in db"
        attachment = self.env["ir.attachment"].create(
            {"name": "Test Attachment", "raw": content}
        )
        self.assertFalse(attachment.store_fname)
        self.assertTrue(attachment.db_datas)
        with attachment.open("rb") as f:
            self.assertEqual(f.read(), content)
        with self.assertRaisesRegex(SystemError, "Write mode is not supported"):
            attachment.open("wb")

    def test_attachment_open_in_filestore(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "ir_attachment.location", "file"
        )
        content = b"This is a test attachment in filestore"
        attachment = self.env["ir.attachment"].create(
            {"name": "Test Attachment", "raw": content}
        )
        self.assertTrue(attachment.store_fname)
        self.assertFalse(attachment.db_datas)
        self.assertEqual(attachment.raw, content)
        with attachment.open("rb") as f:
            self.assertEqual(f.read(), content)
        with attachment.open("wb") as f:
            f.write(b"new")
        # refresh is required while we don't use a file-like object proxy
        # that detect the modification of the content and invalidate the
        # record's cache
        attachment.refresh()
        self.assertEqual(attachment.raw, b"new")
