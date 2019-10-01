# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .common import ProductImageCommonCase


class ProductImageCase(ProductImageCommonCase):
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
        self.assertEqual(self.product_b.variant_image_ids, image)
        self.assertEqual(self.product_c.variant_image_ids, image)

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
        self.assertEqual(self.product_c.variant_image_ids, image)
        # Black product should not have the image
        self.assertEqual(len(self.product_b.variant_image_ids), 0)

    def test_add_image_for_white_and_black_variant(self):
        logo = self.env["product.image.relation"].create(
            {"product_tmpl_id": self.template.id, "image_id": self.logo_image.id}
        )
        image_wh = self.env["product.image.relation"].create(
            {
                "product_tmpl_id": self.template.id,
                "image_id": self.white_image.id,
                "attribute_value_ids": [
                    (6, 0, [self.env.ref("product.product_attribute_value_3").id])
                ],
            }
        )
        image_bk = self.env["product.image.relation"].create(
            {
                "product_tmpl_id": self.template.id,
                "image_id": self.black_image.id,
                "attribute_value_ids": [
                    (6, 0, [self.env.ref("product.product_attribute_value_4").id])
                ],
            }
        )
        # White product should have the white image and the logo
        self.assertEqual(self.product_a.variant_image_ids, image_wh + logo)
        self.assertEqual(self.product_c.variant_image_ids, image_wh + logo)
        # Black product should have the black image and the logo
        self.assertEqual(self.product_b.variant_image_ids, image_bk + logo)
