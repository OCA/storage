# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import os
from odoo.addons.component.tests.common import TransactionComponentCase


class ProductImageCase(TransactionComponentCase):

    def _get_image(self, name):
        path = os.path.dirname(os.path.abspath(__file__))
        f = open(os.path.join(path, 'static', name))
        return base64.b64encode(f.read())

    def _create_storage_image(self, name):
        return self.env['storage.image'].create({
            'name': name,
            'data': self._get_image(name)
            })

    def setUp(self):
        super(ProductImageCase, self).setUp()
        # Run the test with the demo user in order to check the access right
        self.user = self.env.ref('base.user_demo')
        self.user.write({'groups_id': [
            (4, self.env.ref('storage_image.group_image_manager').id)]})
        self.env = self.env(user=self.user)
        self.template = self.env.ref(
            'product.product_product_4_product_template')
        self.product_a = self.env.ref('product.product_product_4')
        self.product_b = self.env.ref('product.product_product_4b')
        self.product_c = self.env.ref('product.product_product_4c')
        self.logo_image = self._create_storage_image('logo-image.jpg')
        self.white_image = self._create_storage_image('white-image.jpg')
        self.black_image = self._create_storage_image('black-image.jpg')

    def test_available_attribute_value(self):
        # The template have already 5 attribute values
        # see demo data of ipad
        image = self.env['product.image'].new({
            'product_tmpl_id': self.template.id})
        self.assertEqual(len(image.available_attribute_value_ids), 5)

    def test_add_image_for_all_variant(self):
        self.assertEqual(len(self.product_a.variant_image_ids), 0)
        image = self.env['product.image'].create({
            'product_tmpl_id': self.template.id,
            'image_id': self.logo_image.id,
            })
        self.assertEqual(self.product_a.variant_image_ids, image)
        self.assertEqual(self.product_b.variant_image_ids, image)
        self.assertEqual(self.product_c.variant_image_ids, image)

    def test_add_image_for_white_variant(self):
        image = self.env['product.image'].create({
            'product_tmpl_id': self.template.id,
            'image_id': self.white_image.id,
            'attribute_value_ids': [(6, 0, [self.env.ref(
                'product.product_attribute_value_3').id])]
            })
        # White product should have the image
        self.assertEqual(self.product_a.variant_image_ids, image)
        self.assertEqual(self.product_c.variant_image_ids, image)
        # Black product should not have the image
        self.assertEqual(len(self.product_b.variant_image_ids), 0)

    def test_add_image_for_white_and_black_variant(self):
        logo = self.env['product.image'].create({
            'product_tmpl_id': self.template.id,
            'image_id': self.logo_image.id,
            })
        image_wh = self.env['product.image'].create({
            'product_tmpl_id': self.template.id,
            'image_id': self.white_image.id,
            'attribute_value_ids': [(6, 0, [self.env.ref(
                'product.product_attribute_value_3').id])]
            })
        image_bk = self.env['product.image'].create({
            'product_tmpl_id': self.template.id,
            'image_id': self.black_image.id,
            'attribute_value_ids': [(6, 0, [self.env.ref(
                'product.product_attribute_value_4').id])]
            })
        # White product should have the white image and the logo
        self.assertEqual(self.product_a.variant_image_ids, image_wh + logo)
        self.assertEqual(self.product_c.variant_image_ids, image_wh + logo)
        # Black product should have the black image and the logo
        self.assertEqual(self.product_b.variant_image_ids, image_bk + logo)
