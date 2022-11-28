# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.addons.component.tests.common import TransactionComponentCase


class StorageMediaCase(TransactionComponentCase):
    def setUp(self):
        super(StorageMediaCase, self).setUp()
        self.backend = self.env.ref("storage_backend.default_storage_backend")
        self.filename = "test of my_file.txt"
        self.media_type = self.env.ref("storage_media.storage_media_type_iso")

    def test_onchange_name(self):
        media = self.env["storage.media"].create(
            {
                "name": self.filename,
                "backend_id": self.backend.id,
                "media_type_id": self.media_type.id,
            }
        )
        self.assertEqual(media.name, self.filename)
        new_filename = "new file name.txt"
        media.name = new_filename
        media.onchange_name()
        values = media._convert_to_write(media._cache)
        self.assertEqual(values["name"], "new-file-name.txt")

    def test_create_media(self):
        media = self.env["storage.media"].create(
            {
                "name": self.filename,
                "media_type_id": self.media_type.id,
            }
        )
        self.assertEqual(media.file_type, "media")
        self.assertIsNotNone(media.backend_id)
