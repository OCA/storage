# Copyright 2017 Akretion (http://www.akretion.com).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models


class StorageBackend(models.Model):
    _inherit = "storage.backend"

    @property
    def _server_env_fields(self):
        env_fields = super()._server_env_fields
        env_fields.update(
            {
                "aws_host": {},
                "aws_bucket": {},
                "aws_access_key_id": {},
                "aws_secret_access_key": {},
                "aws_region": {},
                "aws_other_region": {},
                "aws_cache_control": {},
                "aws_file_acl": {},
            }
        )
        return env_fields
