# Copyright 2026 Camptocamp SA
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.addons.component.tests.common import TransactionComponentCase


class TestStorageFileIsPublic(TransactionComponentCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend = cls.env["storage.backend"].create(
            {"name": "Test backend", "backend_type": "filesystem"}
        )
        cls.storage_file = cls.env["storage.file"].create(
            {
                "name": "test-public.txt",
                "backend_id": cls.backend.id,
                "data": b"aGVsbG8=",  # "hello" base64
            }
        )

    def test_reflects_backend_flag(self):
        self.assertFalse(self.storage_file.is_public)
        self.backend.is_public = True
        self.assertTrue(self.storage_file.is_public)

    def test_search_true(self):
        self.backend.is_public = True
        result = self.env["storage.file"].search(
            [("is_public", "=", True), ("id", "=", self.storage_file.id)]
        )
        self.assertIn(self.storage_file, result)

    def test_search_false(self):
        self.backend.is_public = False
        result = self.env["storage.file"].search(
            [("is_public", "=", False), ("id", "=", self.storage_file.id)]
        )
        self.assertIn(self.storage_file, result)

    def test_search_with_two_backends(self):
        public_backend = self.env["storage.backend"].create(
            {
                "name": "Public backend",
                "backend_type": "filesystem",
                "is_public": True,
            }
        )
        public_file = self.env["storage.file"].create(
            {
                "name": "public.txt",
                "backend_id": public_backend.id,
                "data": b"aGVsbG8=",
            }
        )
        result = self.env["storage.file"].search([("is_public", "=", True)])
        self.assertIn(public_file, result)
        self.assertNotIn(self.storage_file, result)
