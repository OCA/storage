# Copyright 2025 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.fs_field import fields as fs_fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    fs_folder_field = fs_fields.FsFolder()

    def initialize_folder(self):
        """Initialize the folder field with a default value."""
        self.ensure_one()
        if not self.fs_folder_field:
            self.fs_folder_field.initialize()
