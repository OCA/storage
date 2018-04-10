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
            ('sftp', 'SFTP'),
            ],
        required=True)
    directory_path = fields.Char(
        sparse="data",
        help="Relative path to the directory to store the file")

    # SFTP specific fields
    sftp_public_base_url = fields.Char(string='Public url', sparse="data")
    sftp_server = fields.Char(string='SFTP host', sparse="data")
    sftp_port = fields.Integer(string='SFTP port', default=22, sparse="data")
    sftp_dir_path = fields.Char(
        string='Remote path',
        help='Dir on the server where to store files',
        sparse="data")
    sftp_login = fields.Char(
        string='SFTP login',
        help='Login to connect to sftp server',
        sparse="data")

    def store(self, relative_path, datas, is_base64=True, **kwargs):
        if is_base64:
            datas = base64.b64decode(datas)
        return self.store_data(relative_path, datas, **kwargs)

    def store_data(self, relative_path, datas, **kwargs):
        _logger.debug(
            'Backend Storage ID: %s type %s: Write file %s',
            self.backend_type,
            self.id,
            relative_path)
        return self._forward('store_data', relative_path, datas, **kwargs)

    def retrieve_data(self, relative_path, **kwargs):
        _logger.debug(
            'Backend Storage ID: %s type %s: Read file %s',
            self.backend_type,
            self.id,
            relative_path)
        return self._forward('retrieve_data', relative_path, **kwargs)

    def _forward(self, method, *args, **kwargs):
        self.ensure_one()
        with self.work_on(self._name) as work:
            adapter = work.component(usage=self.backend_type)
            return getattr(adapter, method)(*args, **kwargs)
