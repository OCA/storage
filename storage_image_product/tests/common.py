# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import os

from odoo.addons.component.tests.common import SavepointComponentCase


class ProductImageCommonCase(SavepointComponentCase):
    def _get_image(self, name):
        path = os.path.dirname(os.path.abspath(__file__))
        f = open(os.path.join(path, "static", name))
        return base64.b64encode(f.read())

    def _create_storage_image(self, name):
        return self.env["storage.image"].create(
            {"name": name, "data": self._get_image(name)}
        )

    def setUp(self):
        super(ProductImageCommonCase, self).setUp()
        # Run the test with the demo user in order to check the access right
        self.user = self.env.ref("base.user_demo")
        self.user.write(
            {
                "groups_id": [
                    (4, self.env.ref("storage_image.group_image_manager").id)
                ]
            }
        )
        self.env = self.env(user=self.user)
        self.template = self.env.ref(
            "product.product_product_4_product_template"
        )
        self.product_a = self.env.ref("product.product_product_4")
        self.product_b = self.env.ref("product.product_product_4b")
        self.product_c = self.env.ref("product.product_product_4c")
        self.logo_image = self._create_storage_image("logo-image.jpg")
        self.white_image = self._create_storage_image("white-image.jpg")
        self.black_image = self._create_storage_image("black-image.jpg")
