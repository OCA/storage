# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class StorageFileReplace(models.TransientModel):
    _inherit = "storage.file.replace"

    image_id = fields.Many2one("storage.image")

    @api.model
    def default_get(self, fields_list):
        """'default_get' method overloaded."""
        res = super().default_get(fields_list)
        active_model = self.env.context.get("active_model")
        if active_model == "storage.image":
            active_id = self.env.context.get("active_id")
            image = self.env["storage.image"].browse(active_id)
            res.update(
                {
                    "image_id": image.id,
                    "file_id": image.file_id.id,
                }
            )
        return res

    def confirm(self):
        res = super().confirm()
        if self.image_id and self.data:
            self.image_id.file_id = self._get_file_from_data()
        return res
