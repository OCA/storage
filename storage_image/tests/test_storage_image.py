# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# Copyright 2021 Camptocamp (http://www.camptocamp.com).
# @author Iván Todorovich <ivan.todorovich@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


import base64
from urllib import parse

import requests_mock

from odoo.exceptions import AccessError

from .common import StorageImageCommonCase


class StorageImageCase(StorageImageCommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Demo file
        raw_data = cls._get_file_content("static/akretion-logo.png")
        cls.filesize = len(raw_data)
        cls.filedata = base64.b64encode(raw_data)
        cls.filename = "akretion-logo.png"

    def test_create_and_read_image(self):
        image = self._create_storage_image(self.filename, self.filedata)
        self.assertEqual(image.data, self.filedata)
        self.assertEqual(image.mimetype, "image/png")
        self.assertEqual(image.extension, ".png")
        self.assertEqual(image.filename, "akretion-logo")
        url = parse.urlparse(image.url)
        self.assertEqual(
            url.path, "/storage.file/akretion-logo-%d.png" % image.file_id.id
        )
        self.assertEqual(image.file_size, self.filesize)
        self.assertEqual(self.backend.id, image.backend_id.id)

    def test_create_thumbnail(self):
        image = self._create_storage_image(self.filename, self.filedata)
        self.assertIsNotNone(image.image_medium_url)
        self.assertIsNotNone(image.image_small_url)
        self._check_thumbnail(image)

    def test_create_specific_thumbnail(self):
        image = self._create_storage_image(self.filename, self.filedata)
        thumbnail = image.get_or_create_thumbnail(100, 100, "my-image-thumbnail")
        self.assertEqual(thumbnail.url_key, "my-image-thumbnail")
        self.assertEqual(thumbnail.relative_path[0:26], "my-image-thumbnail_100_100")

        # Check that method will return the same thumbnail
        # Check also that url_key have been slugified
        new_thumbnail = image.get_or_create_thumbnail(100, 100, "My Image Thumbnail")
        self.assertEqual(new_thumbnail.id, thumbnail.id)

        # Check that method will return a new thumbnail
        new_thumbnail = image.get_or_create_thumbnail(
            100, 100, "My New Image Thumbnail"
        )
        self.assertNotEqual(new_thumbnail.id, thumbnail.id)

    def test_name_onchange(self):
        image = self.env["storage.image"].new({"name": "Test-of image_name.png"})
        image.onchange_name()
        self.assertEqual(image.name, "test-of-image_name.png")
        self.assertEqual(image.alt_name, "Test of image name")

    def test_unlink(self):
        image = self._create_storage_image(self.filename, self.filedata)
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
            self._create_storage_image(self.filename, self.filedata)

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
            image = self._create_storage_image(self.filename, self.filedata)
            self.assertEqual(len(m.request_history), 2)
            urls = [x.url for x in m.request_history]
            self.assertIn(
                "http://pilbox:8888/?url=test/akretion-logo-%s.png"
                "&w=128&h=128&mode=fill&fmt=webp" % image.file_id.id,
                urls,
            )
            self.assertIn(
                "http://pilbox:8888/?url=test/akretion-logo-%s.png"
                "&w=64&h=64&mode=fill&fmt=webp" % image.file_id.id,
                urls,
            )
