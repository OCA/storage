# Copyright 2026 Camptocamp SA
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64

from odoo.tests.common import HttpCase, tagged


@tagged("-at_install", "post_install")
class TestStorageFileController(HttpCase):
    """Test the /storage.file/ controller with public/private and odoo/external."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.data = b"Hello, storage!"
        cls.filedata = base64.b64encode(cls.data)
        cls.backend_odoo_public = cls.env["storage.backend"].create(
            {
                "name": "Odoo Public",
                "backend_type": "filesystem",
                "served_by": "odoo",
                "is_public": True,
                "filename_strategy": "name_with_id",
            }
        )
        cls.backend_odoo_private = cls.env["storage.backend"].create(
            {
                "name": "Odoo Private",
                "backend_type": "filesystem",
                "served_by": "odoo",
                "is_public": False,
                "filename_strategy": "name_with_id",
            }
        )
        cls.backend_ext_public = cls.env["storage.backend"].create(
            {
                "name": "Ext Public (no CDN)",
                "backend_type": "filesystem",
                "served_by": "external",
                "base_url": "",
                "is_public": True,
                "filename_strategy": "name_with_id",
            }
        )
        cls.backend_ext_private = cls.env["storage.backend"].create(
            {
                "name": "Ext Private (no CDN)",
                "backend_type": "filesystem",
                "served_by": "external",
                "base_url": "",
                "is_public": False,
                "filename_strategy": "name_with_id",
            }
        )
        cls.file_odoo_public = cls.env["storage.file"].create(
            {
                "name": "pub-odoo.txt",
                "backend_id": cls.backend_odoo_public.id,
                "data": cls.filedata,
            }
        )
        cls.file_odoo_private = cls.env["storage.file"].create(
            {
                "name": "priv-odoo.txt",
                "backend_id": cls.backend_odoo_private.id,
                "data": cls.filedata,
            }
        )
        cls.file_ext_public = cls.env["storage.file"].create(
            {
                "name": "pub-ext.txt",
                "backend_id": cls.backend_ext_public.id,
                "data": cls.filedata,
            }
        )
        cls.file_ext_private = cls.env["storage.file"].create(
            {
                "name": "priv-ext.txt",
                "backend_id": cls.backend_ext_private.id,
                "data": cls.filedata,
            }
        )
        cls.internal_user = (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Storage Test User",
                    "login": "storage_test_user",
                    "password": "storage_test_user",
                    "groups_id": [
                        (4, cls.env.ref("base.group_user").id),
                    ],
                }
            )
        )

    def _url_for(self, storage_file):
        return f"/storage.file/{storage_file.slug}"

    # ---- Public user (anonymous) ----

    def test_public_user_odoo_public(self):
        """Public user + public odoo backend -> 200."""
        resp = self.url_open(self._url_for(self.file_odoo_public))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, self.data)

    def test_public_user_odoo_private(self):
        """Public user + private odoo backend -> 404."""
        resp = self.url_open(self._url_for(self.file_odoo_private))
        self.assertEqual(resp.status_code, 404)

    def test_public_user_ext_public(self):
        """Public user + public external backend (no CDN) -> 200."""
        resp = self.url_open(self._url_for(self.file_ext_public))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, self.data)

    def test_public_user_ext_private(self):
        """Public user + private external backend (no CDN) -> 404."""
        resp = self.url_open(self._url_for(self.file_ext_private))
        self.assertEqual(resp.status_code, 404)

    # ---- Internal (authenticated) user ----

    def test_internal_user_odoo_public(self):
        """Internal user + public odoo backend -> 200."""
        self.authenticate("storage_test_user", "storage_test_user")
        resp = self.url_open(self._url_for(self.file_odoo_public))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, self.data)

    def test_internal_user_odoo_private(self):
        """Internal user + private odoo backend -> 200."""
        self.authenticate("storage_test_user", "storage_test_user")
        resp = self.url_open(self._url_for(self.file_odoo_private))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, self.data)

    def test_internal_user_ext_public(self):
        """Internal user + public external backend (no CDN) -> 200."""
        self.authenticate("storage_test_user", "storage_test_user")
        resp = self.url_open(self._url_for(self.file_ext_public))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, self.data)

    def test_internal_user_ext_private(self):
        """Internal user + private external backend (no CDN) -> 200."""
        self.authenticate("storage_test_user", "storage_test_user")
        resp = self.url_open(self._url_for(self.file_ext_private))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, self.data)
