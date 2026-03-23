# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# Copyright 2019 Camptocamp SA (http://www.camptocamp.com).
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


class StorageBackend(models.Model):
    _name = "storage.backend"
    _inherit = ["storage.backend", "server.env.mixin"]

    def _compute_has_validation(self):
        # with server_env
        # this code can be triggered
        # before a backend_type has been set
        # get_adapter() can't work without backend_type
        no_type_storage = self.filtered(lambda storage: not storage.backend_type)
        no_type_storage.has_validation = False
        return super(StorageBackend, self - no_type_storage)._compute_has_validation()

    @property
    def _server_env_fields(self):
        return {"backend_type": {}, "directory_path": {}}
