# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.tests.common import TransactionComponentCase


class StorageMediaCase(TransactionComponentCase):
    def setUp(self):
        super(StorageMediaCase, self).setUp()
        self.filename = "test of my_file.txt"

    def test_onchange_name(self):
        media = self.env["storage.media"].create(
            {"name": self.filename, "backend_id": self.backend_id}
        )
        self.assetEqual(media.name, self.filename)
        new_filename = "new file_name.txt"
        media.name = new_filename
        media._onchange_name()
        values = media._convert_to_write(media._cache)
        self.assertEqual(values["name"], "new-file-name.txt")

    def test_create_media(self):
        media = self.env["storage.media"].create({"name": self.filename})
        self.assertEqual(media.file_type, "media")
        self.assertIsNotNone(media.backend_id)
