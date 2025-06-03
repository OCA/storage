# Copyright 2025 ACSONE SA/NV (http://acsone.eu).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.exceptions import UserError, ValidationError

from odoo.addons.base.tests.common import BaseCommon


class TestFsStorage(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend = cls.env.ref("fs_storage.fs_storage_demo")

    def test_is_fs_name_valid(self):
        self.assertFalse(self.backend.is_fs_name_valid(r'my\/:*?"<>| directory'))
        self.assertTrue(self.backend.is_fs_name_valid("my directory"))
        with self.assertRaises(UserError):
            self.backend.is_fs_name_valid(
                r'my\/:*?"<>| directory', raise_if_invalid=True
            )

    def test_sanitize_fs_item_name(self):
        self.backend.fs_name_sanitization_replace_char = "_"
        sanitized = self.backend.sanitize_fs_item_name("m/y dir*", "_")
        self.assertEqual(sanitized, "m_y dir_")
        sanitized = self.backend.sanitize_fs_item_name("m/y dir*", None)
        self.assertEqual(sanitized, "m_y dir_")
        sanitized = self.backend.sanitize_fs_item_name("m/y dir*", "")
        self.assertEqual(sanitized, "my dir")
        sanitized = self.backend.sanitize_fs_item_name("m/y dir*", "-")
        self.assertEqual(sanitized, "m-y dir-")
        sanitized = self.backend.sanitize_fs_item_name("/y dir*", " ")
        self.assertEqual(sanitized, "y dir")
        with self.assertRaises(ValidationError):
            self.backend.fs_name_sanitization_replace_char = "/"

        sanitized = self.backend.sanitize_fs_item_names(["/y dir*", "sub/dir"], " ")
        self.assertEqual(sanitized, ["y dir", "sub dir"])
