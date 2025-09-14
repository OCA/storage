# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class MicrosoftDriveAccountReset(models.TransientModel):
    _name = "microsoft.drive.account.reset"
    _description = "Microsoft Drive Account Reset"

    user_id = fields.Many2one("res.users", required=True)

    def reset_account(self):
        self.user_id._set_microsoft_drive_auth_tokens(False, False, 0)
