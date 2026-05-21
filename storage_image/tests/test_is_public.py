# Copyright 2026 Camptocamp SA
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from .common import StorageImageCommonCase


class TestStorageImageIsPublic(StorageImageCommonCase):
    def setUp(self):
        super().setUp()
        self.storage_image = self._create_storage_image_from_file(
            "static/akretion-logo.png"
        )

    def test_is_public_reflects_backend(self):
        self.assertFalse(self.storage_image.is_public)
        self.backend.sudo().is_public = True
        self.assertTrue(self.storage_image.is_public)

    def test_is_public_search(self):
        self.backend.sudo().is_public = True
        result = self.env["storage.image"].search(
            [("is_public", "=", True), ("id", "=", self.storage_image.id)]
        )
        self.assertEqual(self.storage_image, result)
