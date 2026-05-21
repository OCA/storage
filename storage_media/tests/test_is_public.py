# Copyright 2026 Camptocamp SA
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.addons.component.tests.common import TransactionComponentCase


class TestStorageMediaIsPublic(TransactionComponentCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend = cls.env.ref("storage_backend.default_storage_backend")
        cls.media = cls.env["storage.media"].create(
            {"name": "test-media.txt", "backend_id": cls.backend.id}
        )

    def test_is_public_reflects_backend(self):
        self.backend.sudo().is_public = False
        self.assertFalse(self.media.is_public)
        self.backend.sudo().is_public = True
        self.assertTrue(self.media.is_public)

    def test_is_public_search(self):
        self.backend.sudo().is_public = True
        result = self.env["storage.media"].search(
            [("is_public", "=", True), ("id", "=", self.media.id)]
        )
        self.assertEqual(self.media, result)
