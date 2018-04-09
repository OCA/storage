# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
import logging
from functools import wraps
from odoo import fields, models
_logger = logging.getLogger(__name__)


class StorageBackend(models.Model):
    _name = 'storage.backend'
    _inherit = ['keychain.backend', 'collection.base']
    _backend_name = 'storage_backend'

    name = fields.Char(required=True)
    backend_type = fields.Selection(
        selection=[
            ('filestore', 'Filestore'),
            ('amazon_s3', 'Amazon S3'),
            ('sftp', 'SFTP'),
            ])
    served_by = fields.Selection(
        selection=[
            ('odoo', 'Odoo'),
            ('external', 'External'),
            ])

    # Filestore specific fields
    filestore_public_base_url = fields.Char(sparse="data")
    filestore_base_path = fields.Char(sparse="data")

    # Amazon specific fields
    aws_bucket = fields.Char(sparse="data")
    aws_directory = fields.Char(sparse="data")
    aws_access_key = fields.Char(sparse="data")
    aws_host = fields.Char(sparse="data")
    aws_cloudfront_domain = fields.Char(sparse="data")
    aws_cloudfront_domain_include_directory = fields.Boolean(sparse="data")

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

    def store(self, name, datas, is_base64=True, **kwargs):
        if is_base64:
            datas = base64.b64decode(datas)
        return self.store_data(name, datas, **kwargs)

    def store_data(self, name, datas, **kwargs):
        return self._forward('store_data', name, datas, **kwargs)

    def get_external_url(self, name, **kwargs):
        self.ensure_one()
        if self.served_by =='external':
            return self._forward('get_external_url', name, **kwargs)
        else:
            raise UserError('This backend do not provide external url')

    def retrieve_data(self, name, **kwargs):
        return self._forward('retrieve_data', name, **kwargs)

    def _forward(self, method, *args, **kwargs):
        self.ensure_one()
        with self.work_on(self._name) as work:
            adapter = work.component(usage=self.backend_type)
            return getattr(adapter, method)(*args, **kwargs)
