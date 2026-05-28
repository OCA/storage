# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.addons.component.tests.common import TransactionComponentCase


class StorageMediaCase(TransactionComponentCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend = cls.env.ref("storage_backend.default_storage_backend")
        cls.filename = "test of my_file.txt"

    def test_onchange_name(self):
        media = self.env["storage.media"].create(
            {"name": self.filename, "backend_id": self.backend.id}
        )
        self.assertEqual(media.name, self.filename)
        new_filename = "new file name.txt"
        media.name = new_filename
        media.onchange_name()
        values = media._convert_to_write(media._cache)
        self.assertEqual(values["name"], "new-file-name.txt")

    def test_create_media(self):
        media = self.env["storage.media"].create({"name": self.filename})
        self.assertEqual(media.file_type, "media")
        self.assertIsNotNone(media.backend_id)

    def test_unlink(self):
        media = self.env["storage.media"].create({"name": self.filename})
        stfile = media.file_id
        media.unlink()
        self.assertEqual(stfile.to_delete, True)
        self.assertEqual(stfile.active, False)

    def test_default_backend_id_on_form(self):
        """Creating a media without backend_id uses the configured default."""
        media = self.env["storage.media"].create({"name": "default-test.txt"})
        self.assertEqual(media.backend_id, self.backend)

    def test_default_backend_id_from_param(self):
        """storage.media.backend_id param overrides backend on create."""
        other_backend = self.env["storage.backend"].create(
            {
                "name": "Media Backend",
                "backend_type": "filesystem",
                "filename_strategy": "name_with_id",
            }
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "storage.media.backend_id", str(other_backend.id)
        )
        media = self.env["storage.media"].create({"name": "test.txt"})
        self.assertEqual(media.backend_id.id, other_backend.id)
