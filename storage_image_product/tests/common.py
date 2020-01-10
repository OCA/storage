# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import os

from odoo.addons.component.tests.common import SavepointComponentCase


class ProductImageCommonCase(SavepointComponentCase):
    @staticmethod
    def _get_file_content(name, base_path=None, as_binary=False):
        path = base_path or os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(path, "fixture", name), "rb") as f:
            data = f.read()
        if as_binary:
            return data
        return base64.b64encode(data)

    @classmethod
    def _create_storage_image(cls, name):
        return cls.env["storage.image"].create(
            {"name": name, "data": cls._get_file_content(name)}
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.template = cls.env.ref("product.product_product_4_product_template")
        cls.product_a = cls.env.ref("product.product_product_4")
        cls.product_b = cls.env.ref("product.product_product_4b")
        cls.product_c = cls.env.ref("product.product_product_4c")
        cls.logo_image = cls._create_storage_image("logo-image.jpg")
        cls.white_image = cls._create_storage_image("white-image.jpg")
        cls.black_image = cls._create_storage_image("black-image.jpg")
