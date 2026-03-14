# Copyright 2024 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).


from odoo import models


class ResUsers(models.Model):
    _inherit = "res.users"

    def _get_oauth2_client_params(self):
        self.ensure_one()
        get_param = self.env["ir.config_parameter"].sudo().get_param
        return {
            "client_id": get_param("microsoft_drive_client_id"),
            "client_secret": get_param("microsoft_drive_client_secret"),
            "token_endpoint": get_param("microsoft_account.token_endpoint"),
        }

    def _get_oauth2_params(self):
        self.ensure_one()
        params = self._get_oauth2_client_params()
        if self.microsoft_drive_oauth2_non_interactive:
            params["grant_type"] = "client_credentials"
            params["scope"] = "https://graph.microsoft.com/.default"
        else:
            params["grant_type"] = "refresh_token"
            params["scope"] = self.env["microsoft.service"]._get_drive_scope()
            access_token = self.microsoft_drive_token
            rtoken = self.microsoft_drive_rtoken
            expires_at = -1
            if self.microsoft_drive_token_validity:
                # Convert datetime to timestamp
                # This is needed for compatibility with authlib
                # which expects an integer timestamp.
                # If the token validity is not set, we use -1 to indicate no expiry.
                expires_at = int(self.microsoft_drive_token_validity.timestamp())
            token = {
                "access_token": access_token,
                "refresh_token": rtoken,
                "expires_at": expires_at,
            }
            params["token"] = token
        return params
