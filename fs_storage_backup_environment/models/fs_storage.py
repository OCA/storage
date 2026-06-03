# Copyright 2023 ACSONE SA/NV (https://www.acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from __future__ import annotations

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class FSStorage(models.Model):
    _inherit = "fs.storage"

    @property
    def _server_env_fields(self):
        env_fields = super()._server_env_fields
        env_fields.update(
            {
                "use_for_backup": {},
                "backup_include_filestore": {},
                "backup_filename_format": {"no_default_field": False},
                "backup_keep_time": {"no_default_field": False},
                "backup_dir": {"no_default_field": False},
            }
        )
        return env_fields
