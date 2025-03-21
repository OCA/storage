# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError


class FsStorage(models.Model):
    _inherit = "fs.storage"

    use_as_default_for_fs_contents = fields.Boolean(
        help="If checked, this storage will be used to store the content of the "
        "external filesystem fields by default. ",
        default=False,
    )

    @api.constrains("use_as_default_for_fs_contents")
    def _check_use_as_default_for_fs_contents(self):
        # constrains are checked in python since values can be provided by
        # the server environment
        defaults = self.search([]).filtered("use_as_default_for_fs_contents")
        if len(defaults) > 1:
            raise ValidationError(
                _("Only one storage can be used as default for filesystem contents.")
            )

    @property
    def _server_env_fields(self):
        env_fields = super()._server_env_fields
        env_fields.update(
            {
                "use_as_default_for_fs_contents": {},
            }
        )
        return env_fields

    @api.model
    @tools.ormcache()
    def get_storage_code_for_fs_content_fallback(self):
        storages = (
            self.sudo()
            .search([])
            .filtered_domain([("use_as_default_for_fs_contents", "=", True)])
        )
        if storages:
            return storages[0].code
        return None

    @api.model
    def get_default_storage_code_for_fs_content(self, model_name, field_name):
        """
        Return the code of the default storage for the content of the
        external filesystem fields.
        """
        storage_code = self.get_storage_code_by_model_field(model_name, field_name)
        if not storage_code:
            storage_code = self.get_storage_code_for_fs_content_fallback()
        if not storage_code:
            raise ValueError(
                _(
                    "No default storage found for the content of the external "
                    "filesystem fields for model %(model)s and field %(field)s. "
                    "Please set a default storage in the filesystem storage "
                    "configuration.",
                    model=model_name,
                    field=field_name,
                )
            )
        return storage_code
