# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64

from odoo.tests import Form

from odoo.addons.component.tests.common import TransactionComponentCase


class TestProductMedia(TransactionComponentCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.media = cls.env["storage.media"].create(
            {"name": "doc.txt", "data": base64.b64encode(b"doc")}
        )
        cls.product = cls.env["product.product"].create({"name": "Media product"})
        cls.relation = cls.env["product.media.relation"].create(
            {
                "media_id": cls.media.id,
                "product_tmpl_id": cls.product.product_tmpl_id.id,
            }
        )

    def test_archived_relation_listed_on_template(self):
        product_tmpl = self.product.product_tmpl_id
        view = "storage_media_product.product_template_only_form_view"
        self.media.active = False
        self.assertFalse(self.relation.media_active)
        self.assertEqual(len(Form(product_tmpl, view=view).media_ids), 1)

    def test_archived_relation_listed_on_variant(self):
        view = "storage_media_product.product_normal_form_view"
        self.media.active = False
        self.assertEqual(len(Form(self.product, view=view).variant_media_ids), 1)
