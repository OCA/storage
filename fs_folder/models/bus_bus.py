# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, models


class BusBus(models.Model):
    _inherit = "bus.bus"

    @api.model
    def _notify_fs_folder_modified(self, record, field_name, modified_path=None):
        """Notify the bus that a fs_folder field has been modified."""
        message = {
            "res_id": record.id,
            "res_model": record._name,
            "field_name": field_name,
            "type": "folder_modified",
            "path": modified_path,
        }
        self.env.user.partner_id._bus_send("fs_folder_notification", message)
