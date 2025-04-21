# Copyright 2017 Akretion (http://www.akretion.com).
# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import io

from PIL import Image

from odoo.addons.base.tests.common import BaseCommon


class TestFsProductMultiImage(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.white_image = cls._create_image(16, 16, color="#FFFFFF")
        cls.logo_image = cls._create_image(16, 16, color="#FFA500")
        cls.product_public_category = cls.env["product.public.category"].create(
            {
                "name": "Public Category",
            }
        )
        cls.image_white = cls.env["fs.image"].create(
            {
                "image": {
                    "filename": "white.png",
                    "content": base64.b64encode(cls.white_image),
                }
            }
        )
        cls.image_logo = cls.env["fs.image"].create(
            {
                "image": {
                    "filename": "logo.png",
                    "content": base64.b64encode(cls.logo_image),
                }
            }
        )
        cls.image_tag = cls.env["image.tag"].create(
            {
                "name": "Icon",
                "apply_on": "public.category",
            }
        )
        model_xmlids = """
        fs_product_multi_image.model_fs_product_category_image,
        fs_product_multi_image.model_fs_product_image
        """
        cls.temp_dir = cls.env["fs.storage"].create(
            {
                "name": "Temp FS Storage",
                "protocol": "memory",
                "code": "mem_dir",
                "directory_path": "/tmp/",
                "model_xmlids": model_xmlids,
            }
        )

    @classmethod
    def _create_image(cls, width, height, color="#4169E1", img_format="PNG"):
        f = io.BytesIO()
        Image.new("RGB", (width, height), color).save(f, img_format)
        f.seek(0)
        return f.read()

    def _create_multiple_images(self):
        logo = self.env["fs.product.public.category.image"].create(
            {
                "public_category_id": self.product_public_category.id,
                "tag_id": self.image_tag.id,
                "image_id": self.image_logo.id,
                "sequence": 10,
                "link_existing": True,
            }
        )
        image_wh = self.env["fs.product.public.category.image"].create(
            {
                "public_category_id": self.product_public_category.id,
                "tag_id": self.image_tag.id,
                "image_id": self.image_white.id,
                "sequence": 2,
                "link_existing": True,
            }
        )
        return logo, image_wh

    def test_add_image_for_product_public_category(self):
        logo, image_wh = self._create_multiple_images()
        # White product should have the white image and the logo
        self.assertEqual(self.product_public_category.image_ids, image_wh + logo)
