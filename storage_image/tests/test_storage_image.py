# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import os
from urllib import parse

import requests_mock

from odoo.exceptions import AccessError

from odoo.addons.component.tests.common import TransactionComponentCase


class StorageImageCase(TransactionComponentCase):
    def setUp(self):
        super(StorageImageCase, self).setUp()
        # FIXME: remove this, should have explicit permission tests
        # Run the test with the demo user in order to check the access right
        self.user = self.env.ref("base.user_demo")
        self.user.write(
            {"groups_id": [(4, self.env.ref("storage_image.group_image_manager").id)]}
        )
        self.env = self.env(user=self.user)

        self.backend = self.env.ref("storage_backend.default_storage_backend")
        path = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(path, "static/akretion-logo.png"), "rb") as f:
            data = f.read()
        self.filesize = len(data)
        self.filedata = base64.b64encode(data)
        self.filename = "akretion-logo.png"

    def _create_storage_image(self):
        return self.env["storage.image"].create(
            {"name": self.filename, "image_medium_url": self.filedata}
        )

    def _check_thumbnail(self, image):
        self.assertEqual(len(image.thumbnail_ids), 2)
        medium, small = image.thumbnail_ids
        self.assertEqual(medium.size_x, 128)
        self.assertEqual(medium.size_y, 128)
        self.assertEqual(small.size_x, 64)
        self.assertEqual(small.size_y, 64)

    def test_create_and_read_image(self):
        image = self._create_storage_image()
        self.assertEqual(image.data, self.filedata)
        self.assertEqual(image.mimetype, u"image/png")
        self.assertEqual(image.extension, u".png")
        self.assertEqual(image.filename, u"akretion-logo")
        url = parse.urlparse(image.url)
        self.assertEqual(
            url.path, "/storage.file/akretion-logo-%d.png" % image.file_id.id
        )
        self.assertEqual(image.file_size, self.filesize)
        self.assertEqual(self.backend.id, image.backend_id.id)

    def test_create_thumbnail(self):
        image = self._create_storage_image()
        self.assertIsNotNone(image.image_medium_url)
        self.assertIsNotNone(image.image_small_url)
        self._check_thumbnail(image)

    def test_create_specific_thumbnail(self):
        image = self._create_storage_image()
        thumbnail = image.get_or_create_thumbnail(100, 100, u"my-image-thumbnail")
        self.assertEqual(thumbnail.url_key, u"my-image-thumbnail")
        self.assertEqual(thumbnail.relative_path[0:26], u"my-image-thumbnail_100_100")

        # Check that method will return the same thumbnail
        # Check also that url_key have been slugified
        new_thumbnail = image.get_or_create_thumbnail(100, 100, u"My Image Thumbnail")
        self.assertEqual(new_thumbnail.id, thumbnail.id)

        # Check that method will return a new thumbnail
        new_thumbnail = image.get_or_create_thumbnail(
            100, 100, u"My New Image Thumbnail"
        )
        self.assertNotEqual(new_thumbnail.id, thumbnail.id)

    def test_name_onchange(self):
        image = self.env["storage.image"].new({"name": "Test-of image_name.png"})
        image.onchange_name()
        self.assertEqual(image.name, u"test-of-image_name.png")
        self.assertEqual(image.alt_name, u"Test of image name")

    def test_unlink(self):
        image = self._create_storage_image()
        stfile = image.file_id
        thumbnail_files = image.thumbnail_ids.mapped("file_id")
        image.unlink()
        self.assertEqual(stfile.to_delete, True)
        self.assertEqual(stfile.active, False)
        for thumbnail_file in thumbnail_files:
            self.assertEqual(thumbnail_file.to_delete, True)
            self.assertEqual(thumbnail_file.active, False)

    def test_no_manager_user_can_not_write(self):
        # Remove access rigth to demo user
        group_manager = self.env.ref("storage_image.group_image_manager")
        self.user = self.env.ref("base.user_demo")
        self.user.sudo().write({"groups_id": [(3, group_manager.id)]})
        with self.assertRaises(AccessError):
            self._create_storage_image()

    def test_create_thumbnail_pilbox(self):
        self.env["ir.config_parameter"].sudo().create(
            {
                "key": "storage.image.resize.server",
                "value": "http://pilbox:8888?url={url}&w={width}&h={height}"
                "&mode=fill&fmt={fmt}",
            }
        )
        self.env["ir.config_parameter"].sudo().create(
            {"key": "storage.image.resize.format", "value": "webp"}
        )
        backend = self.env["storage.backend"].sudo().browse([self.backend.id])
        backend.served_by = "external"
        backend.base_url = "test"
        with requests_mock.mock() as m:
            m.get("http://pilbox:8888?", text="data")
            image = self._create_storage_image()
            self.assertEqual(len(m.request_history), 2)
            self.assertEqual(
                m.request_history[0].url,
                "http://pilbox:8888/?url=test/akretion-logo-%s.png"
                "&w=128&h=128&mode=fill&fmt=webp" % image.file_id.id,
            )
            self.assertEqual(
                m.request_history[1].url,
                "http://pilbox:8888/?url=test/akretion-logo-%s.png"
                "&w=64&h=64&mode=fill&fmt=webp" % image.file_id.id,
            )
