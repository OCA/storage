# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# Copyright 2019 Camptocamp SA (http://www.camptocamp.com).
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class StorageBackend(models.Model):
    _inherit = "storage.backend"

    backend_type = fields.Selection(
        selection_add=[("sftp", "SFTP")], ondelete={"sftp": "set default"}
    )
    sftp_server = fields.Char(string="SFTP Host")
    sftp_port = fields.Integer(string="SFTP Port", default=22)
    sftp_auth_method = fields.Selection(
        string="SFTP Authentification Method",
        selection=[("pwd", "Password"), ("ssh_key", "Private key")],
        default="pwd",
        required=True,
    )
    sftp_login = fields.Char(
        string="SFTP Login", help="Login to connect to sftp server"
    )
    sftp_password = fields.Char(string="SFTP Password")
    sftp_ssh_private_key = fields.Text(
        string="SSH private key",
        help="SSH private key for authentication. Accepts:\n"
        "- Key content: paste the full private key\n"
        "- File path: '/path/to/id_rsa' or '~/.ssh/id_rsa'\n"
        "Note: It's recommended to use file paths or env variables "
        "instead of storing keys directly. See `server_environment` docs.",
    )
    sftp_verify_hostkey = fields.Boolean(
        string="Verify Host Key",
        default=False,
        help="Verify the server's host key against a known value. "
        "Recommended for security to prevent MITM attacks.",
    )
    sftp_hostkey = fields.Text(
        string="Server Host Key",
        help="Expected host key of the SFTP server. Accepts:\n"
        "- Key content: 'ssh-rsa AAAAB3...'\n"
        "- File path: '/path/to/known_hosts' or '~/.ssh/known_hosts'\n"
        "You can obtain the key with: ssh-keyscan -t rsa hostname",
    )
    sftp_legacy_algorithms = fields.Boolean(
        string="Enable Legacy SSH Algorithms",
        default=False,
        help="Enable ssh-rsa and other legacy algorithms for older SFTP servers "
        "that don't support modern key exchange algorithms.",
    )
    sftp_verbose_logging = fields.Boolean(
        string="Verbose Logging",
        default=False,
        help="Enable detailed logging of SFTP connection details including "
        "server capabilities, cipher negotiation, and key fingerprints. "
        "Useful for debugging connection issues.",
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
                "sftp_verify_hostkey": {},
                "sftp_hostkey": {},
                "sftp_legacy_algorithms": {},
                "sftp_verbose_logging": {},
            }
        )
        return env_fields
