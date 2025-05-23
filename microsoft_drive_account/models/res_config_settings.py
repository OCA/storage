# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    drive_microsoft_client_id = fields.Char(
        "Microsoft Drive Client_id",
        config_parameter="microsoft_drive_client_id",
        default="",
    )
    drive_microsoft_client_secret = fields.Char(
        "Microsoft Drive Client_key",
        config_parameter="microsoft_drive_client_secret",
        default="",
    )
    drive_microsoft_client_scope = fields.Char(
        "Microsoft Drive Scope",
        config_parameter="microsoft_drive_client_scope",
        default="",
    )
