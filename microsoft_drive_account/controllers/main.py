# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import json

from werkzeug.exceptions import BadRequest

from odoo import http
from odoo.http import request

from odoo.addons.microsoft_account.controllers import main


class MicrosoftAuth(main.MicrosoftAuth):
    @http.route("/ms_drive_account/status", type="json", auth="user", methods=["POST"])
    def check_user_connected(self, from_url=None, **kwargs):
        """Check if the user is connected to Microsoft Drive.

        This route is called to verify if the user has a valid connection
        to Microsoft Drive before performing any operations that require
        access to the user's Microsoft Drive account from the User Interface.

        The function returns a dictionary with the connection status and
        a url to redirect the user to the Microsoft Drive authentication
        page if they are not connected.
        """
        return {
            "status": request.env.user.microsoft_drive_status,
            "url": request.env.user.get_drive_authentication_url(from_url=from_url),
        }

    @http.route()
    def oauth2callback(self, **kw):
        # we need to handle the case where the user is redirected to the
        # callback URL for the specific drive service
        state = json.loads(kw.get("state", "{}"))
        service = state.get("s")
        url_return = state.get("f")
        base_url = request.env["ir.config_parameter"].sudo().get_param("web.base.url")
        redirect_uri = f"{base_url}/microsoft_account/authentication"
        if not service or (kw.get("code") and not url_return):
            raise BadRequest()

        if service != "drive":
            return super().oauth2callback(**kw)
        if kw.get("code"):
            access_token, refresh_token, ttl = request.env[
                "microsoft.service"
            ]._get_microsoft_tokens(kw["code"], service, redirect_uri)
            request.env.user._set_microsoft_drive_auth_tokens(
                access_token, refresh_token, ttl
            )
            return request.redirect(url_return)
        if kw.get("error"):
            url = f"{url_return}?error={kw.get('error')}"
            return request.redirect(url)
        url = f"{url_return}?error=Unknown_error"
        return request.redirect(url)
