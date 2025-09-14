from datetime import datetime as dt
from functools import partial

from odoo import SUPERUSER_ID, api, models
from odoo.modules.registry import Registry


class FSStorage(models.Model):
    _inherit = "fs.storage"

    def _get_fs_options(self):
        options = super()._get_fs_options()
        if self.protocol == "msgd":
            params = self.env.user._get_oauth2_params()
            options["oauth2_client_params"] = params
        return options

    def _get_filesystem(self):
        fs = super()._get_filesystem()
        if self.protocol == "msgd":
            # Using `_get_root_filesystem` here would result in infinite recursion.
            root_fs = fs
            while hasattr(root_fs, "fs"):
                root_fs = fs.fs
            client = root_fs.client
            client.register_compliance_hook(
                "refresh_token_response",
                partial(
                    self.update_refresh_token_on_user,
                    client=client,
                    db_name=self._cr.dbname,
                    user_id=self.env.user.id,
                ),
            )
        return fs

    @api.model
    def update_refresh_token_on_user(
        self, res, client=None, db_name=None, user_id=None
    ):
        with Registry(db_name).cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            user = env["res.users"].browse(user_id)
            if user:
                token = client.parse_response_token(res)
                ts = token.get("expires_at", False)
                valid_untill = dt.fromtimestamp(ts) if ts else False
                user.write(
                    {
                        "microsoft_drive_token": token.get("access_token", False),
                        "microsoft_drive_rtoken": token.get("refresh_token", False),
                        "microsoft_drive_token_validity": valid_untill,
                    }
                )
        return res
