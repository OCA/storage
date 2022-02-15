# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# Copyright 2019 Camptocamp SA (http://www.camptocamp.com).
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import api, fields, models

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
    base_url_for_files = fields.Char(compute="_compute_base_url_for_files", store=True)

    def write(self, vals):
        # Ensure storage file URLs are up to date
        clear_url_cache = False
        url_related_fields = (
            "served_by",
            "base_url",
            "directory_path",
            "url_include_directory_path",
        )
        for fname in url_related_fields:
            if fname in vals:
                clear_url_cache = True
                break
        res = super().write(vals)
        if clear_url_cache:
            self.action_recompute_base_url_for_files()
        return res

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

    @api.depends(
        "served_by",
        "base_url",
        "directory_path",
        "url_include_directory_path",
    )
    def _compute_base_url_for_files(self):
        for record in self:
            record.base_url_for_files = record._get_base_url_for_files()

    def _get_base_url_for_files(self):
        """Retrieve base URL for files."""
        backend = self.sudo()
        parts = []
        if backend.served_by == "external":
            parts = [backend.base_url or ""]
            if backend.url_include_directory_path and backend.directory_path:
                parts.append(backend.directory_path)
        return "/".join(parts)

    def action_recompute_base_url_for_files(self):
        """Refresh base URL for files.

        Rationale: all the params for computing this URL might come from server env.
        When this is the case, the URL - being stored - might be out of date.
        This is because changes to server env fields are not detected at startup.
        Hence, let's offer an easy way to promptly force this manually when needed.
        """
        self._compute_base_url_for_files()
        self.env["storage.file"].invalidate_cache(["url"])

    def _get_base_url_from_param(self):
        base_url_param = (
            "report.url" if self.env.context.get("print_report_pdf") else "web.base.url"
        )
        return self.env["ir.config_parameter"].sudo().get_param(base_url_param)

    def _get_url_for_file(self, storage_file):
        """Return final full URL for given file."""
        backend = self.sudo()
        if backend.served_by == "odoo":
            parts = [
                self._get_base_url_from_param(),
                "storage.file",
                storage_file.slug,
            ]
        else:
            parts = [backend.base_url_for_files or "", storage_file.relative_path or ""]
        return "/".join([x.rstrip("/") for x in parts if x])

    def _register_hook(self):
        super()._register_hook()
        self.search([]).action_recompute_base_url_for_files()
        _logger.info("storage.backend base URL for files refreshed")
