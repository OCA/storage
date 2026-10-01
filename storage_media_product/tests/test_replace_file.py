# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64

from odoo.tests import Form

from odoo.addons.component.tests.common import TransactionComponentCase


class TestReplaceFile(TransactionComponentCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.media = cls.env["storage.media"].create(
            {"name": "old.txt", "data": base64.b64encode(b"old")}
        )
        cls.product = cls.env["product.product"].create({"name": "Media product"})
        cls.category = cls.env["product.category"].create(
            {"name": "Media categ", "media_ids": [(4, cls.media.id)]}
        )
        cls.relation = cls.env["product.media.relation"].create(
            {
                "media_id": cls.media.id,
                "product_tmpl_id": cls.product.product_tmpl_id.id,
            }
        )

    def _replace_media_file(self, keep_history, keep_relations=False):
        wiz_form = Form(
            self.env["storage.file.replace"].with_context(
                active_model="storage.media", active_id=self.media.id
            ),
            view="storage_media.storage_file_replace_view_form",
        )
        wiz_form.file_name = "new.txt"
        wiz_form.data = base64.b64encode(b"new")
        wiz_form.keep_history = keep_history
        if keep_history:
            wiz_form.keep_relations = keep_relations
        wiz_form.save().confirm()

    def test_replace_keep_history_and_relations(self):
        old_file = self.media.file_id
        self._replace_media_file(keep_history=True, keep_relations=True)
        # The relations of the archived media are hidden by default
        product_tmpl = self.product.product_tmpl_id.with_context(active_test=False)
        self.assertEqual(len(product_tmpl.media_ids), 2)
        archived_relation = product_tmpl.media_ids - self.relation
        self.assertFalse(archived_relation.active)
        self.assertEqual(archived_relation.media_id.file_id, old_file)
        self.assertTrue(self.relation.active)
        self.assertNotEqual(self.relation.media_id.file_id, old_file)
        self.assertEqual(
            self.category.with_context(active_test=False).media_ids,
            self.media | archived_relation.media_id,
        )

    def test_replace_keep_history_only(self):
        self._replace_media_file(keep_history=True)
        product_tmpl = self.product.product_tmpl_id.with_context(active_test=False)
        self.assertEqual(product_tmpl.media_ids, self.relation)
        self.assertEqual(
            self.category.with_context(active_test=False).media_ids, self.media
        )

    def test_replace_no_history(self):
        self._replace_media_file(keep_history=False)
        product_tmpl = self.product.product_tmpl_id.with_context(active_test=False)
        self.assertEqual(product_tmpl.media_ids, self.relation)

    def test_keep_relations_visibility(self):
        wiz_form = Form(
            self.env["storage.file.replace"].with_context(
                active_model="storage.media", active_id=self.media.id
            ),
            view="storage_media.storage_file_replace_view_form",
        )
        self.assertTrue(wiz_form.keep_relations_visible)
        wiz_form.keep_history = False
        self.assertFalse(wiz_form.keep_relations_visible)
