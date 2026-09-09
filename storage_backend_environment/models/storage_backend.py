# Copyright 2017 Akretion (http://www.akretion.com).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models


class StorageBackend(models.Model):
    _name = "storage.backend"
    _inherit = ["storage.backend", "server.env.mixin"]

    @property
    def _server_env_fields(self):
        return {"backend_type": {}, "directory_path": {}}
