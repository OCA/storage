# Copyright 2017 Akretion (http://www.akretion.com).
# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import io

from PIL import Image

from odoo.tests.common import TransactionCase


class TestFsProductMultiImage(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.white_image = cls._create_image(16, 16, color="#FFFFFF")
        cls.black_image = cls._create_image(16, 16, color="#000000")
        cls.logo_image = cls._create_image(16, 16, color="#FFA500")
        cls.template = cls.env.ref("product.product_product_4_product_template")
        cls.product_a = cls.env.ref("product.product_product_4")
        cls.product_b = cls.env.ref("product.product_product_4b")
        cls.product_c = cls.env.ref("product.product_product_4c")
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
        cls.image_black = cls.env["fs.image"].create(
            {
                "image": {
                    "filename": "black.png",
                    "content": base64.b64encode(cls.black_image),
                }
            }
        )
        cls.is_sale_addon_installed = cls.env["ir.module.module"].search(
            [("name", "=", "sale"), ("state", "=", "installed")]
        )

    def setUp(self):
        super().setUp()
        self.temp_dir = self.env["fs.storage"].create(
            {
                "name": "Temp FS Storage",
                "protocol": "memory",
                "code": "mem_dir",
                "directory_path": "/tmp/",
                "model_xmlids": "fs_product_multi_image.model_fs_product_category_image,"
                "fs_product_multi_image.model_fs_product_image",
            }
        )

    @classmethod
    def _create_image(cls, width, height, color="#4169E1", img_format="PNG"):
        f = io.BytesIO()
        Image.new("RGB", (width, height), color).save(f, img_format)
        f.seek(0)
        return f.read()

    def test_available_attribute_value(self):
        # The template have already 5 attribute values
        # see demo data of ipad
        image = self.env["fs.product.image"].new({"product_tmpl_id": self.template.id})
        expected = 4
        if self.is_sale_addon_installed:
            expected += 1
        self.assertEqual(len(image.available_attribute_value_ids), expected)

    def test_add_image_for_all_variant(self):
        self.assertEqual(len(self.product_a.variant_image_ids), 0)
        image = self.env["fs.product.image"].create(
            {
                "product_tmpl_id": self.template.id,
                "specific_image": {
                    "filename": "white.png",
                    "content": base64.b64encode(self.white_image),
                },
            }
        )
        self.assertEqual(self.product_a.image.getvalue(), self.white_image)
        self.assertEqual(self.product_a.variant_image_ids, image)
        self.assertEqual(self.product_a.main_image_id, image)
        self.assertEqual(self.product_b.image.getvalue(), self.white_image)
        self.assertEqual(self.product_b.variant_image_ids, image)
        self.assertEqual(self.product_b.main_image_id, image)
        self.assertEqual(self.product_c.image.getvalue(), self.white_image)
        self.assertEqual(self.product_c.variant_image_ids, image)
        self.assertEqual(self.product_c.main_image_id, image)

    def test_add_image_for_white_variant(self):
        image = self.env["fs.product.image"].create(
            {
                "product_tmpl_id": self.template.id,
                "image_id": self.image_white.id,
                "attribute_value_ids": [
                    (6, 0, [self.env.ref("product.product_attribute_value_3").id])
                ],
            }
        )
        # White product should have the image
        self.assertEqual(self.product_a.variant_image_ids, image)
        self.assertEqual(self.product_a.main_image_id, image)
        self.assertEqual(self.product_c.variant_image_ids, image)
        self.assertEqual(self.product_c.main_image_id, image)
        # Black product should not have the image
        self.assertEqual(len(self.product_b.variant_image_ids), 0)
        self.assertFalse(self.product_b.main_image_id)

    def _create_multiple_images(self):
        logo = self.env["fs.product.image"].create(
            {
                "product_tmpl_id": self.template.id,
                "image_id": self.image_logo.id,
                "sequence": 10,
                "link_existing": True,
            }
        )
        image_wh = self.env["fs.product.image"].create(
            {
                "product_tmpl_id": self.template.id,
                "image_id": self.image_white.id,
                "attribute_value_ids": [
                    (6, 0, [self.env.ref("product.product_attribute_value_3").id])
                ],
                "sequence": 2,
                "link_existing": True,
            }
        )
        image_bk = self.env["fs.product.image"].create(
            {
                "product_tmpl_id": self.template.id,
                "image_id": self.image_black.id,
                "attribute_value_ids": [
                    (6, 0, [self.env.ref("product.product_attribute_value_4").id])
                ],
                "sequence": 1,
                "link_existing": True,
            }
        )
        return logo, image_wh, image_bk

    def test_add_image_for_white_and_black_variant(self):
        logo, image_wh, image_bk = self._create_multiple_images()
        # White product should have the white image and the logo
        self.assertEqual(self.product_a.variant_image_ids, image_wh + logo)
        self.assertEqual(self.product_c.variant_image_ids, image_wh + logo)
        # Black product should have the black image and the logo
        self.assertEqual(self.product_b.variant_image_ids, image_bk + logo)

    def test_image_variant_sequence(self):
        logo, image_wh, image_bk = self._create_multiple_images()
        # White product should have the white image and the logo
        self.assertEqual(self.product_a.variant_image_ids, image_wh + logo)
        # white product should have images sorted by sequence
        self.assertListEqual(
            self.product_a.variant_image_ids.mapped("sequence"),
            [image_wh.sequence, logo.sequence],
        )
        # change sequence
        image_wh.sequence = 20
        logo.sequence = 10
        self.assertListEqual(
            self.product_a.variant_image_ids.mapped("sequence"),
            [logo.sequence, image_wh.sequence],
        )

    def _test_main_images(self, expected):
        for image, products in expected:
            for prod in products:
                self.assertEqual(prod.image.getvalue(), image)

    def test_main_image_and_urls(self):
        logo, image_wh, image_bk = self._create_multiple_images()
        # Template should have the one w/ lower sequence
        expected = ((self.black_image, self.template),)
        self._test_main_images(expected)
        # Should have different main images
        expected = (
            (self.white_image, self.product_a + self.product_c),
            (self.black_image, self.product_b),
        )
        self._test_main_images(expected)
        # Change image order, change main image
        logo.sequence = 0
        image_wh.sequence = 10
        expected = ((self.logo_image, self.template),)
        self._test_main_images(expected)
        expected = (
            (self.logo_image, self.product_a + self.product_c),
            (self.logo_image, self.product_b),
        )
        self._test_main_images(expected)

    def test_main_image_attribute(self):
        """
        Attach the image to the template and check the first image of the
        variant is the one with same attributes
        """
        self.env["fs.product.image"].create(
            {
                "product_tmpl_id": self.template.id,
                "image_id": self.image_logo.id,
                "sequence": 1,
                "link_existing": True,
            }
        )
        self.env["fs.product.image"].create(
            {
                "product_tmpl_id": self.template.id,
                "image_id": self.image_white.id,
                "attribute_value_ids": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("product.product_attribute_value_4").id,
                            self.env.ref("product.product_attribute_value_1").id,
                        ],
                    )
                ],
                "sequence": 10,
                "link_existing": True,
            }
        )
        # The variant should not take the only with the lowest sequence but
        # the one with same attributes
        expected = ((self.white_image, self.product_b),)
        self._test_main_images(expected)
        expected = ((self.logo_image, self.product_c + self.product_a),)
        self._test_main_images(expected)

    def test_drop_template_attribute_value_propagation_to_image(self):
        black_image = self.env["fs.product.image"].create(
            {
                "product_tmpl_id": self.template.id,
                "image_id": self.image_black.id,
                "attribute_value_ids": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("product.product_attribute_value_4").id,
                            self.env.ref("product.product_attribute_value_1").id,
                        ],
                    )
                ],
                "sequence": 10,
                "link_existing": True,
            }
        )
        # Remove Color black from variant tab:
        self.template.attribute_line_ids.sudo().filtered(
            lambda x: x.display_name == "Color"
        ).value_ids -= self.env.ref("product.product_attribute_value_4")
        # Attribute black is removed from image:
        self.assertTrue(
            self.env.ref("product.product_attribute_value_4")
            not in black_image.attribute_value_ids
        )

        # Remove Leg attribute line from variant tab:
        self.template.attribute_line_ids.sudo().filtered(
            lambda x: x.display_name == "Legs"
        ).unlink()
        # Product image attribute values from Legs are removed:
        self.assertTrue(
            self.env.ref("product.product_attribute_value_1")
            not in black_image.attribute_value_ids
        )
