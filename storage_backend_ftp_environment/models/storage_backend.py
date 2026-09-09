# Copyright 2021 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models


class StorageBackend(models.Model):
    _inherit = "storage.backend"

    @property
    def _server_env_fields(self):
        env_fields = super()._server_env_fields
        env_fields.update(
            {
                "ftp_password": {},
                "ftp_login": {},
                "ftp_server": {},
                "ftp_port": {},
                "ftp_encryption": {},
                "ftp_security": {},
                "ftp_passive": {},
            }
        )
        return env_fields
