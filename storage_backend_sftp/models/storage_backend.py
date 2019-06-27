# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StorageBackend(models.Model):
    _inherit = "storage.backend"

    backend_type = fields.Selection(selection_add=[("sftp", "SFTP")])
    sftp_password = fields.Char(string="Password")
    sftp_login = fields.Char(
        string="Login", help="Login to connect to sftp server"
    )
    sftp_server = fields.Char(string="Host")
    sftp_port = fields.Integer(string="Port", default=22)
    sftp_auth_method = fields.Selection(
        string="Authentification Method",
        selection=[("pwd", "Password"), ("ssh_key", "Private key")],
        default="pwd",
        required=True,
    )
