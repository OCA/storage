# Copyright 2023 ACSONE SA/NV (https://www.acsone.eu).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
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
                "optimizes_directory_path": {},
                "autovacuum_gc": {},
                "base_url": {},
                "is_directory_path_in_url": {},
                "use_x_sendfile_to_serve_internal_url": {},
                "use_as_default_for_attachments": {},
                "force_db_for_default_attachment_rules": {},
                "use_filename_obfuscation": {},
                "model_xmlids": {},
                "field_xmlids": {},
            }
        )
        return env_fields
