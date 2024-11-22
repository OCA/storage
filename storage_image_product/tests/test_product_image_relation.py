# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import os

from odoo.addons.storage_image.tests.common import StorageImageCommonCase


class ProductImageCase(StorageImageCommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.template = cls.env.ref("product.product_product_4_product_template")
        cls.product_a = cls.env.ref("product.product_product_4")
        cls.product_b = cls.env.ref("product.product_product_4b")
        cls.product_c = cls.env.ref("product.product_product_4c")
        cls.base_path = os.path.dirname(os.path.abspath(__file__))
        cls.logo_image = cls._create_storage_image_from_file("fixture/logo-image.jpg")
        cls.white_image = cls._create_storage_image_from_file("fixture/white-image.jpg")
        cls.black_image = cls._create_storage_image_from_file("fixture/black-image.jpg")

    def test_available_attribute_value(self):
        # The template have already 5 attribute values
        # see demo data of ipad
        image = self.env["product.image.relation"].new(
            {"product_tmpl_id": self.template.id}
        )
        self.assertEqual(len(image.available_attribute_value_ids), 5)

    def test_add_image_for_all_variant(self):
        self.assertEqual(len(self.product_a.variant_image_ids), 0)
        image = self.env["product.image.relation"].create(
            {"product_tmpl_id": self.template.id, "image_id": self.logo_image.id}
        )
        self.assertEqual(self.product_a.variant_image_ids, image)
        self.assertEqual(self.product_a.main_image_id, self.logo_image)
        self.assertEqual(self.product_b.variant_image_ids, image)
        self.assertEqual(self.product_b.main_image_id, self.logo_image)
        self.assertEqual(self.product_c.variant_image_ids, image)
        self.assertEqual(self.product_c.main_image_id, self.logo_image)

    def test_add_image_for_white_variant(self):
        image = self.env["product.image.relation"].create(
            {
                "product_tmpl_id": self.template.id,
                "image_id": self.white_image.id,
                "attribute_value_ids": [
                    (6, 0, [self.env.ref("product.product_attribute_value_3").id])
                ],
            }
        )
        # White product should have the image
        self.assertEqual(self.product_a.variant_image_ids, image)
        self.assertEqual(self.product_a.main_image_id, self.white_image)
        self.assertEqual(self.product_c.variant_image_ids, image)
        self.assertEqual(self.product_c.main_image_id, self.white_image)
        # Black product should not have the image
        self.assertEqual(len(self.product_b.variant_image_ids), 0)
        self.assertFalse(self.product_b.main_image_id)

    def _create_multiple_images(self):
        logo = self.env["product.image.relation"].create(
            {
                "product_tmpl_id": self.template.id,
                "image_id": self.logo_image.id,
                "sequence": 10,
            }
        )
        image_wh = self.env["product.image.relation"].create(
            {
                "product_tmpl_id": self.template.id,
                "image_id": self.white_image.id,
                "attribute_value_ids": [
                    (6, 0, [self.env.ref("product.product_attribute_value_3").id])
                ],
                "sequence": 2,
            }
        )
        image_bk = self.env["product.image.relation"].create(
            {
                "product_tmpl_id": self.template.id,
                "image_id": self.black_image.id,
                "attribute_value_ids": [
                    (6, 0, [self.env.ref("product.product_attribute_value_4").id])
                ],
                "sequence": 1,
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

    def _test_main_images_and_urls(self, expected):
        for image, products in expected:
            for prod in products:
                self.assertEqual(prod.main_image_id, image)
                for size in ("small", "medium"):
                    prod_fname = fname = f"image_{size}_url"
                    if prod._name == "product.product":
                        prod_fname = "variant_" + fname
                    self.assertEqual(prod[prod_fname], image[fname])

    def test_main_image_and_urls(self):
        logo, image_wh, image_bk = self._create_multiple_images()
        # Template should have the one w/ lower sequence
        expected = ((self.black_image, self.template),)
        self._test_main_images_and_urls(expected)
        # Should have different main images
        expected = (
            (self.white_image, self.product_a + self.product_c),
            (self.black_image, self.product_b),
        )
        self._test_main_images_and_urls(expected)
        # Change image order, change main image
        logo.sequence = 0
        image_wh.sequence = 10
        expected = ((self.logo_image, self.template),)
        self._test_main_images_and_urls(expected)
        expected = (
            (self.logo_image, self.product_a + self.product_c),
            (self.logo_image, self.product_b),
        )
        self._test_main_images_and_urls(expected)

    def test_main_image_attribute(self):
        """
        Attach the image to the template and check the first image of the
        variant is the one with same attributes
        """
        self.env["product.image.relation"].create(
            {
                "product_tmpl_id": self.template.id,
                "image_id": self.logo_image.id,
                "sequence": 1,
            }
        )
        self.env["product.image.relation"].create(
            {
                "product_tmpl_id": self.template.id,
                "image_id": self.white_image.id,
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
            }
        )
        # The variant should not take the only with the lowest sequence but
        # the one with same attributes
        expected = ((self.white_image, self.product_b),)
        self._test_main_images_and_urls(expected)
        expected = ((self.logo_image, self.product_c + self.product_a),)
        self._test_main_images_and_urls(expected)

    def test_drop_template_attribute_value_propagation_to_image(self):
        black_image = self.env["product.image.relation"].create(
            {
                "product_tmpl_id": self.template.id,
                "image_id": self.black_image.id,
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
