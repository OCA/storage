# -*- coding: utf-8 -*-

from odoo.tests.common import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestWebDAVUpload(HttpCase):
    def setUp(self):
        super().setUp()
        self.api_user = self.env["res.users"].create(
            {
                "name": "WebDAV Upload User",
                "login": "webdav_upload_user",
                "email": "webdav_upload@example.com",
            }
        )
        # res.users.apikeys stores only the hash; _generate returns the raw key.
        self.api_key = (
            self.env["res.users.apikeys"]
            .with_user(self.api_user)
            ._generate("dav", "WebDAV Upload Key")
        )

    def _put(self, path, body=b"statement", headers=None):
        hdrs = {"Content-Type": "application/octet-stream"}
        hdrs.update(headers or {})
        return self.url_open(f"/upload/dav/{path}", data=body, headers=hdrs)

    def test_options_needs_no_auth(self):
        """Clients must be able to probe capabilities before holding a key."""
        response = self.url_open("/upload/dav/anything", method="OPTIONS")
        self.assertEqual(response.status_code, 200)
        self.assertIn("PROPFIND", response.headers.get("Allow", ""))

    def test_put_without_auth_is_rejected(self):
        response = self._put("statement.csv")
        self.assertEqual(response.status_code, 401)

    def test_put_with_bad_auth_is_rejected(self):
        response = self._put(
            "statement.csv", headers={"Authorization": "Bearer not-a-real-key"}
        )
        self.assertEqual(response.status_code, 401)

    def test_put_with_malformed_auth_is_rejected(self):
        response = self._put("statement.csv", headers={"Authorization": "Token abc"})
        self.assertEqual(response.status_code, 401)

    def test_put_with_valid_auth_creates_attachment(self):
        response = self._put(
            "statement.csv",
            body=b"date,amount\n2026-01-01,100.00\n",
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.headers.get("Location", "").startswith("/attachment/"))

        attachment = self.env["ir.attachment"].search(
            [("name", "=", "statement.csv")], limit=1
        )
        self.assertTrue(attachment.exists())
        self.assertFalse(attachment.public)

    def test_empty_body_is_rejected(self):
        response = self._put(
            "empty.csv", body=b"", headers={"Authorization": f"Bearer {self.api_key}"}
        )
        self.assertEqual(response.status_code, 400)

    def test_traversal_segment_is_rejected(self):
        response = self._put(
            "../escape.csv", headers={"Authorization": f"Bearer {self.api_key}"}
        )
        self.assertIn(response.status_code, (400, 404))

    def test_deactivated_user_key_is_rejected(self):
        self.api_user.active = False
        response = self._put(
            "statement.csv", headers={"Authorization": f"Bearer {self.api_key}"}
        )
        self.assertEqual(response.status_code, 401)
