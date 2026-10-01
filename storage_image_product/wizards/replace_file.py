# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


class StorageFileReplace(models.TransientModel):
    _inherit = "storage.file.replace"

    def _has_replaced_relations(self):
        return super()._has_replaced_relations() or bool(self.image_id)

    def _copy_replaced_relations(self, owner, archived):
        res = super()._copy_replaced_relations(owner, archived)
        if owner._name == "storage.image":
            self._copy_replaced_image_relations(owner, archived)
        return res

    def _copy_replaced_image_relations(self, image, archived_image):
        for model in ("product.image.relation", "category.image.relation"):
            relations = (
                self.env[model]
                .sudo()
                .with_context(active_test=False)
                .search([("image_id", "=", image.id)])
            )
            relations.copy({"image_id": archived_image.id})
