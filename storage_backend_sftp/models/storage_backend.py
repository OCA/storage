# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# Copyright 2019 Camptocamp SA (http://www.camptocamp.com).
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StorageBackend(models.Model):
    _inherit = "storage.backend"

    backend_type = fields.Selection(
        selection_add=[("sftp", "SFTP")], ondelete={"sftp": "set default"}
    )
    sftp_server = fields.Char(string="SFTP Host")
    sftp_port = fields.Integer(string="Port", default=22)
    sftp_auth_method = fields.Selection(
        string="Authentification Method",
        selection=[("pwd", "Password"), ("ssh_key", "Private key")],
        default="pwd",
        required=True,
    )
    sftp_login = fields.Char(string="Login", help="Login to connect to sftp server")
    sftp_password = fields.Char(string="Password")
    sftp_ssh_private_key = fields.Text(
        string="SSH private key",
        help="It's recommended to not store the key here "
        "but to provide it via secret env variable. "
        "See `server_environment` docs.",
    )

    @property
    def _server_env_fields(self):
        env_fields = super()._server_env_fields
        env_fields.update(
            {
                "sftp_password": {},
                "sftp_login": {},
                "sftp_server": {},
                "sftp_port": {},
                "sftp_auth_method": {},
                "sftp_ssh_private_key": {},
            }
        )
        return env_fields
