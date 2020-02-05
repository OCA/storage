# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# Copyright 2019 Camptocamp SA (http://www.camptocamp.com).
# @author Simone Orsi <simone.orsi@camptocamp.com>
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

    @property
    def _server_env_fields(self):
        env_fields = super()._server_env_fields
        env_fields.update(
            {
                "filename_strategy": {},
                "served_by": {},
                "base_url": {},
                "url_include_directory_path": {},
            }
        )
        return env_fields

    _default_backend_xid = "storage_backend.default_storage_backend"

    @classmethod
    def _get_backend_id_from_param(cls, env, param_name, default_fallback=True):
        backend_id = None
        param = env["ir.config_parameter"].sudo().get_param(param_name)
        if param:
            if param.isdigit():
                backend_id = int(param)
            elif "." in param:
                backend = env.ref(param, raise_if_not_found=False)
                if backend:
                    backend_id = backend.id
        if not backend_id and default_fallback:
            backend = env.ref(cls._default_backend_xid, raise_if_not_found=False)
            if backend:
                backend_id = backend.id
            else:
                _logger.warn("No backend found, no default fallback found.")
        return backend_id
