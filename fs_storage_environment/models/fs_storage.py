# Copyright 2023 ACSONE SA/NV (https://www.acsone.eu).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import logging
import os

from odoo import fields, models

_logger = logging.getLogger(__name__)


class FSStorage(models.Model):
    _name = "fs.storage"
    _inherit = ["fs.storage", "server.env.mixin"]

    eval_options_from_env = fields.Boolean(
        string="Resolve env vars",
        help="""Resolve options values starting with $ from environment variables. e.g
            {
                "endpoint_url": "$AWS_ENDPOINT_URL",
            }
            """,
    )

    _server_env_section_name_field = "code"

    @property
    def _server_env_fields(self):
        return {
            "protocol": {},
            "options": {},
            "directory_path": {},
            "eval_options_from_env": {},
        }

    def _eval_options_from_env(self, options):
        values = {}
        for key, value in options.items():
            if isinstance(value, dict):
                values[key] = self._eval_options_from_env(value)
            elif isinstance(value, str) and value.startswith("$"):
                env_variable_name = value[1:]
                env_variable_value = os.getenv(env_variable_name)
                if env_variable_value is not None:
                    values[key] = env_variable_value
                else:
                    values[key] = value
                    _logger.warning(
                        "Environment variable %s is not set for fs_storage %s.",
                        env_variable_name,
                        self.display_name,
                    )
            else:
                values[key] = value
        return values

    def _get_fs_options(self):
        # OVERRIDE: to resolve env vars in options
        if not self.eval_options_from_env:
            return super()._get_fs_options()
        return self._eval_options_from_env(self.json_options)
