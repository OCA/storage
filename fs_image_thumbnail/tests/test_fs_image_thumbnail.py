# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import io

from PIL import Image

from odoo.tests.common import TransactionCase

from odoo.addons.fs_image.fields import FSImageValue


class TestFsImageThumbnail(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.white_image = cls._create_image(32, 32, color="#FFFFFF")

        cls.image_attachment = cls.env["ir.attachment"].create(
            {
                "name": "Test Image",
                "datas": base64.b64encode(cls.white_image),
                "mimetype": "image/png",
            }
        )

        cls.fs_image_value = FSImageValue(attachment=cls.image_attachment)
        cls.fs_thumbnail_model = cls.env["fs.thumbnail"]

    def setUp(self):
        super().setUp()
        self.temp_dir = self.env["fs.storage"].create(
            {
                "name": "Temp FS Storage",
                "protocol": "memory",
                "code": "mem_dir",
                "directory_path": "/tmp/",
                "model_xmlids": "fs_image_thumbnail.model_fs_thumbnail",
            }
        )

    @classmethod
    def _create_image(cls, width, height, color="#4169E1", img_format="PNG"):
        f = io.BytesIO()
        Image.new("RGB", (width, height), color).save(f, img_format)
        f.seek(0)
        return f.read()

    def assert_image_size(self, value: bytes, width, height):
        self.assertEqual(Image.open(io.BytesIO(value)).size, (width, height))

    def test_create_multi(self):
        self.assertFalse(self.image_attachment.thumbnail_ids)
        thumbnails = self.fs_thumbnail_model.get_or_create_thumbnails(
            self.fs_image_value, sizes=[(16, 16), (8, 8)], base_name="My super test"
        )[self.fs_image_value]
        self.assertEqual(len(thumbnails), 2)
        self.assertEqual(thumbnails[0].name, "my-super-test_16_16.png")
        self.assert_image_size(thumbnails[0].image.getvalue(), 16, 16)
        self.assertEqual(thumbnails[1].name, "my-super-test_8_8.png")
        self.assert_image_size(thumbnails[1].image.getvalue(), 8, 8)

        self.assertEqual(self.image_attachment.thumbnail_ids, thumbnails)

        # if we call the method again for the same size, we should get the same thumbnail
        new_thumbnails = self.fs_thumbnail_model.get_or_create_thumbnails(
            self.fs_image_value, sizes=[(16, 16), (8, 8)], base_name="My super test"
        )[self.fs_image_value]
        self.assertEqual(new_thumbnails, thumbnails)

    def test_create_with_specific_format(self):
        self.env["ir.config_parameter"].set_param(
            "fs_image_thumbnail.resize_format", "JPEG"
        )
        thumbnail = self.fs_thumbnail_model.get_or_create_thumbnails(
            self.fs_image_value, sizes=[(8, 8)], base_name="My super test"
        )[self.fs_image_value]
        self.assertEqual(thumbnail[0].name, "my-super-test_8_8.jpeg")
        self.assertEqual(thumbnail[0].mimetype, "image/jpeg")
        self.assert_image_size(thumbnail[0].image.getvalue(), 8, 8)
