# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, models


class MicrosoftService(models.AbstractModel):
    _inherit = "microsoft.service"

    @api.model
    def _get_drive_scope(self):
        ICP = self.env["ir.config_parameter"].sudo()
        scope = ICP.get_param(
            "microsoft_drive_client_scope",
            "offline_access openid Files.ReadWrite.All Sites.ReadWrite.All",
        )
        if "offline_access" not in scope:
            scope += " offline_access"
        if "openid" not in scope:
            scope += " openid"
        return scope

    def _get_calendar_scope(self):
        if self.env.context.get("microsoft_drive"):
            return self._get_drive_scope()
        return super()._get_calendar_scope()

    @api.model
    def generate_refresh_token(self, service, authorization_code):
        _self = self
        if service == "drive":
            _self = self.with_context(microsoft_drive=True)
        return super(MicrosoftService, _self).generate_refresh_token(
            service, authorization_code
        )

    @api.model
    def _get_microsoft_tokens(self, authorize_code, service, redirect_uri):
        _self = self
        if service == "drive":
            _self = self.with_context(microsoft_drive=True)
        return super(MicrosoftService, _self)._get_microsoft_tokens(
            authorize_code, service, redirect_uri
        )
