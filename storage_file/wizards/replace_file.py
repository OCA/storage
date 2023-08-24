# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class StorageFileReplace(models.TransientModel):
    _name = "storage.file.replace"
    _description = "Wizard template allowing to replace a storage.file"

    file_id = fields.Many2one("storage.file")
    data = fields.Binary()
    file_name = fields.Char()

    def _get_file_from_data(self):
        file_model = self.env["storage.file"].sudo()
        return file_model.create(
            {
                "backend_id": self.file_id.backend_id.id,
                "data": self.data,
                "name": self.file_name,
            }
        )

    def confirm(self):
        return
