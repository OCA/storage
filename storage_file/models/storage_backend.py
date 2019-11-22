# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class StorageBackend(models.Model):
    _inherit = "storage.backend"

    filename_strategy = fields.Selection(
        selection=[("name_with_id", "Name and ID"), ("hash", "SHA hash")],
        default="name_with_id",
        help=(
            "Strategy to build the name of the file to be stored.\n"
            "Name and ID: will store the file with its name + its id.\n"
            "SHA Hash: will use the hash of the file as filename "
            "(same method as the native attachment storage)"
        ),
    )
    served_by = fields.Selection(
        selection=[("odoo", "Odoo"), ("external", "External")],
        required=True,
        default="odoo",
    )
    base_url = fields.Char(default="")
    is_public = fields.Boolean(
        default=False,
        help="Define if every files stored into this backend are "
        "public or not. Examples:\n"
        "Private: your file/image can not be displayed is the user is "
        "not logged (not available on other website);\n"
        "Public: your file/image can be displayed if nobody is "
        "logged (useful to display files on external websites)",
    )
    url_include_directory_path = fields.Boolean(
        default=False,
        help="Normally the directory_path it's for internal usage. "
        "If this flag is enabled "
        "the path will be used to compute the public URL.",
    )
