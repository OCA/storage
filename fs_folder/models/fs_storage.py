# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
import re

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, ValidationError


class FsStorage(models.Model):
    _inherit = "fs.storage"

    use_as_default_for_fs_contents = fields.Boolean(
        help="If checked, this storage will be used to store the content of the "
        "external filesystem fields by default. ",
        default=False,
    )
    sanitize_fs_name = fields.Boolean(
        help="If checked, the names of the filesystem items created by the fields will "
        "be sanitized. Invalid characters will be replaced by the value provided by "
        "the field 'fs_name_sanitizatio_replace_char'.",
        default=True,
    )
    fs_name_sanitization_replace_char = fields.Char(
        help="The character used to replace the invalid characters in the names of the "
        "filesystem items created by the fields.",
        default="_",
    )

    @api.constrains("fs_name_sanitization_replace_char")
    def _check_fs_name_sanitization_replace_char(self):
        for rec in self:
            rc = rec.fs_name_sanitization_replace_char

            if rc and self._invalid_fs_name_chars_re_pattern.findall(rc):
                raise ValidationError(
                    _("The character to use as replacement can not be one of '%s'")
                    % self._invalid_fs_name_chars
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
    def get_storage_code_for_fs_content_fallback(self) -> str | None:
        storages = (
            self.sudo()
            .search([])
            .filtered_domain([("use_as_default_for_fs_contents", "=", True)])
        )
        if storages:
            return storages[0].code
        return None

    @api.model
    def get_default_storage_code_for_fs_content(self, model_name, field_name) -> str:
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

    @property
    def _invalid_fs_name_chars(self) -> str:
        return r'<>:"/\\|?*\x00-\x1f'

    @property
    def _invalid_fs_name_chars_re_pattern(self) -> re.Pattern:
        pattern = f"[{self._invalid_fs_name_chars}]"
        return re.compile(pattern)

    def is_fs_name_valid(self, name, raise_if_invalid=False) -> bool:
        self.ensure_one()
        invalid = self._invalid_fs_name_chars_re_pattern.findall(name)
        if invalid and raise_if_invalid:
            raise UserError(
                _(
                    "The name '%(name)s' contains invalid characters"
                    " %(invalid_chars)s.\n"
                    "The following chars are not allowed: %(all_invalid_chars)s",
                    name=name,
                    invalid_chars=", ".join(invalid),
                    all_invalid_chars=self._invalid_fs_name_chars,
                )
            )
        return not bool(invalid)

    def is_fs_names_valid(self, names, raise_if_invalid=False) -> bool:
        return all(self.is_fs_name_valid(name, raise_if_invalid) for name in names)

    def sanitize_fs_item_name(self, name, replace_char=None) -> str:
        """Sanitize a filesystem item name by replacing invalid characters with a
        replacement character.

        :param name: the name to sanitize
        :param replace_char: the character to use as replacement. If not provided, the
            value of the field 'fs_name_sanitization_replace_char' will be used.
        :return: the sanitized name
        """
        self.ensure_one()
        if replace_char is None:
            replace_char = self.fs_name_sanitization_replace_char

        return self._invalid_fs_name_chars_re_pattern.sub(
            replace_char, name.strip()
        ).strip()

    def sanitize_fs_item_names(self, names, replace_char=None) -> list[str]:
        """Sanitize a list of filesystem item names by replacing invalid characters with
        a replacement character.

        :param names: the names to sanitize
        :param replace_char: the character to use as replacement. If not provided, the
            value of the field 'fs_name_sanitization_replace_char' will be used.
        :return: the sanitized names
        """
        self.ensure_one()
        return [self.sanitize_fs_item_name(name, replace_char) for name in names]
