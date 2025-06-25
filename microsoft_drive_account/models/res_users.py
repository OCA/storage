# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
import json
from datetime import timedelta

from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    microsoft_drive_rtoken = fields.Char(
        "Microsoft Drive Refresh Token", copy=False, groups="base.group_system"
    )
    microsoft_drive_token = fields.Char(copy=False, groups="base.group_system")
    microsoft_drive_token_validity = fields.Datetime(copy=False)
    microsoft_drive_status = fields.Selection(
        [
            ("not_connected", "Not connected"),
            ("connected", "Connected"),
        ],
        "Microsoft Drive Connection Status",
        default="not_connected",
        copy=False,
        compute="_compute_microsoft_drive_status",
        store=True,
    )

    def _set_microsoft_drive_auth_tokens(
        self, access_token: str, refresh_token: str, ttl: float
    ):
        token_validity = False
        if access_token and ttl:
            token_validity = fields.Datetime.now() + timedelta(seconds=ttl)
        self.write(
            {
                "microsoft_drive_rtoken": refresh_token,
                "microsoft_drive_token": access_token,
                "microsoft_drive_token_validity": token_validity,
            }
        )

    @api.depends("microsoft_drive_rtoken")
    def _compute_microsoft_drive_status(self):
        for user in self:
            user.microsoft_drive_status = (
                "connected" if user.microsoft_drive_rtoken else "not_connected"
            )

    def get_drive_authentication_url(self, from_url: str) -> str:
        microsoft_service = self.env["microsoft.service"].sudo()
        scope = microsoft_service._get_drive_scope()
        base_url = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("web.base.url", default="http://www.odoo.com?NoBaseUrl")
        )
        redirect_uri = f"{base_url}/microsoft_account/authentication"
        return microsoft_service._get_authorize_uri(
            from_url, service="drive", scope=scope, redirect_uri=redirect_uri
        )

    def action_drive_disconnect(self):
        """Disconnect the user from Drive."""
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "microsoft_drive_account.microsoft_drive_reset_account_action"
        )
        py_ctx = json.loads(action.get("context", {}))
        py_ctx.update(
            {
                "default_user_id": self.id,
            }
        )
        action["context"] = py_ctx
        return action
