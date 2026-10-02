# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.tests import Form

from .common import ProductImageCaseMixin, TransactionComponentCase


class TestReplaceFile(TransactionComponentCase, ProductImageCaseMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.image = cls._create_storage_image("logo-image.jpg")
        cls.template = cls.env["product.template"].create({"name": "Image product"})
        cls.category = cls.env["product.category"].create({"name": "Image categ"})
        cls.product_relation = cls.env["product.image.relation"].create(
            {"image_id": cls.image.id, "product_tmpl_id": cls.template.id}
        )
        cls.category_relation = cls.env["category.image.relation"].create(
            {"image_id": cls.image.id, "category_id": cls.category.id}
        )

    def _replace_image_file(self, keep_history, keep_relations=False):
        wiz_form = Form(
            self.env["storage.file.replace"].with_context(
                active_model="storage.image", active_id=self.image.id
            ),
            view="storage_image.storage_file_replace_view_form",
        )
        wiz_form.file_name = "white-image.jpg"
        wiz_form.data = self._get_file_content("white-image.jpg")
        wiz_form.keep_history = keep_history
        if keep_history:
            wiz_form.keep_relations = keep_relations
        wiz_form.save().confirm()

    def _relations(self, model):
        images = self.image | self._archived_image()
        return (
            self.env[model]
            .with_context(active_test=False)
            .search([("image_id", "in", images.ids)])
        )

    def _archived_image(self):
        return self.env["storage.image"].search(
            [("file_id", "=", self.old_file.id), ("active", "=", False)]
        )

    def test_replace_keep_history_and_relations(self):
        self.old_file = self.image.file_id
        self._replace_image_file(keep_history=True, keep_relations=True)
        archived_image = self._archived_image()
        self.assertEqual(len(archived_image), 1)
        self.assertTrue(self.image.active)
        self.assertNotEqual(self.image.file_id, self.old_file)
        for model, current in (
            ("product.image.relation", self.product_relation),
            ("category.image.relation", self.category_relation),
        ):
            archived_relation = self._relations(model) - current
            self.assertEqual(archived_relation.image_id, archived_image)
            self.assertFalse(archived_relation.active)
        # The relations of the archived image are hidden on the product
        self.assertEqual(self.template.image_ids, self.product_relation)
        self.assertEqual(self.template.main_image_id, self.image)

    def test_replace_keep_history_only(self):
        self.old_file = self.image.file_id
        self._replace_image_file(keep_history=True)
        self.assertEqual(len(self._archived_image()), 1)
        self.assertEqual(
            self._relations("product.image.relation"), self.product_relation
        )
        self.assertEqual(
            self._relations("category.image.relation"), self.category_relation
        )
