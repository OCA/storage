# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import models


class FsStorage(models.Model):
    _inherit = "fs.storage"

    @property
    def _server_env_fields(self):
        env_fields = super()._server_env_fields
        env_fields.update(
            {
                "use_as_default_for_fs_contents": {},
            }
        )
        return env_fields
