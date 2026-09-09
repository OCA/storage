# Copyright 2023 ACSONE SA/NV (https://www.acsone.eu).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from __future__ import annotations

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class FSStorage(models.Model):
    _name = "fs.storage"
    _inherit = ["fs.storage", "server.env.mixin"]

    _server_env_section_name_field = "code"

    @property
    def _server_env_fields(self):
        return {
            "protocol": {},
            "options": {},
            "directory_path": {},
            "eval_options_from_env": {},
            "model_xmlids": {},
            "field_xmlids": {},
            "check_connection_method": {},
        }
