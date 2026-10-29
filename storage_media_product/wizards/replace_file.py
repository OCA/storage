# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class StorageFileReplace(models.TransientModel):
    _inherit = "storage.file.replace"

    def _has_replaced_relations(self):
        return super()._has_replaced_relations() or bool(self.media_id)

    def _copy_replaced_relations(self, owner, archived):
        res = super()._copy_replaced_relations(owner, archived)
        if owner._name == "storage.media":
            self._copy_replaced_media_relations(owner, archived)
        return res

    def _copy_replaced_media_relations(self, media, archived_media):
        relations = (
            self.env["product.media.relation"]
            .sudo()
            .with_context(active_test=False)
            .search([("media_id", "=", media.id)])
        )
        relations.copy({"media_id": archived_media.id})
        categories = (
            self.env["product.category"].sudo().search([("media_ids", "in", media.ids)])
        )
        categories.write({"media_ids": [fields.Command.link(archived_media.id)]})
