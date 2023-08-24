# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class StorageFileReplace(models.TransientModel):
    _inherit = "storage.file.replace"

    media_id = fields.Many2one("storage.media")

    @api.model
    def default_get(self, fields_list):
        """'default_get' method overloaded."""
        res = super().default_get(fields_list)
        active_model = self.env.context.get("active_model")
        if active_model == "storage.media":
            active_id = self.env.context.get("active_id")
            media = self.env["storage.media"].browse(active_id)
            res.update(
                {
                    "media_id": media.id,
                    "file_id": media.file_id.id,
                }
            )
        return res

    def confirm(self):
        res = super().confirm()
        if self.media_id and self.data:
            self.media_id.file_id = self._get_file_from_data()
            # TODO remove sudo
            self.media_id.file_id.sudo()._inverse_data()
        return res
