# Copyright 2025 Dixmit
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models

from odoo.addons.fs_folder import fields as fs_fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    fs_folder_field = fs_fields.FsFolder()

    def initialize_folder(self):
        """Initialize the folder field with a default value."""
        self.ensure_one()
        if not self.fs_folder_field:
            self.fs_folder_field.initialize()
