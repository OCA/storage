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
        """Override to include S3 specific fields."""
        fields = super()._server_env_fields
        fields.update(
            {
                "s3_uses_signed_url_for_x_sendfile": {},
                "s3_signed_url_expiration": {},
            }
        )
        return fields
