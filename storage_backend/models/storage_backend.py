# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import base64
from odoo import fields, models
_logger = logging.getLogger(__name__)


class StorageBackend(models.Model):
    _name = 'storage.backend'
    _inherit = ['keychain.backend', 'collection.base']
    _backend_name = 'storage_backend'

    name = fields.Char(required=True)
    backend_type = fields.Selection(
        selection=[
            ('filesystem', 'Filesystem'),
            ],
        required=True)
    directory_path = fields.Char(
        sparse="data",
        help="Relative path to the directory to store the file")

    def add_b64_data(self, relative_path, data, **kwargs):
        return self.add_bin_data(
            relative_path, base64.b64decode(data), **kwargs)

    def get_b64_data(self, relative_path, **kwargs):
        data = self.get_bin_data(relative_path, **kwargs)
        return data and base64.b64encode(data) or ''

    def add_bin_data(self, relative_path, data, **kwargs):
        _logger.debug(
            'Backend Storage ID: %s type %s: Write file %s',
            self.backend_type,
            self.id,
            relative_path)
        return self._forward('add', relative_path, data, **kwargs)

    def get_bin_data(self, relative_path, **kwargs):
        _logger.debug(
            'Backend Storage ID: %s type %s: Read file %s',
            self.backend_type,
            self.id,
            relative_path)
        return self._forward('get', relative_path, **kwargs)

    def _forward(self, method, *args, **kwargs):
        self.ensure_one()
        with self.work_on(self._name) as work:
            adapter = work.component(usage=self.backend_type)
            return getattr(adapter, method)(*args, **kwargs)
