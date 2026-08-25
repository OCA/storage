# Copyright 2021 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class StorageBackend(models.Model):
    _inherit = "storage.backend"

    backend_type = fields.Selection(
        selection_add=[("ftp", "FTP")], ondelete={"ftp": "set default"}
    )
    ftp_server = fields.Char(string="FTP Host")
    ftp_port = fields.Integer(string="FTP Port", default=21)
    ftp_encryption = fields.Selection(
        string="FTP Encryption method",
        selection=[
            ("ftp", "FTP"),
            ("tls", "Implicit FTP over TLS"),
            ("tls_explicit", "Explicit FTP over TLS"),
        ],
        default="ftp",
        required=True,
    )
    ftp_security = fields.Selection(
        string="FTP security option",
        selection=[
            ("none", "None"),
            ("tlsv1", "TLS"),
            ("tlsv1_1", "TLSv1_1"),
            ("tlsv1_2", "TLSv1_2"),
            ("sslv2", "SSLv2"),
            ("sslv23", "SSLv23"),
            ("sslv3", "SSLv3"),
        ],
        default="none",
        required=True,
    )
    ftp_login = fields.Char(string="FTP Login", help="Login to connect to ftp server")
    ftp_password = fields.Char(string="FTP Password")
    ftp_passive = fields.Boolean(string="FTP Passive", default=False)
