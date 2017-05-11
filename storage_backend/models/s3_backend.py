# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import socket
import hashlib
import logging
import base64

from openerp import api, fields, models
from openerp.exceptions import Warning as UserError

logger = logging.getLogger(__name__)

try:
    from fs import s3fs
except ImportError as err:
    logger.debug(err)


class S3StorageBackend(models.Model):
    _inherit = 'storage.backend'
    _backend_name = 'storage_backend_sftp'

    backend_type = fields.Selection(
        selection_add=[('amazon_s3', 'Amazon S3')])

    aws_bucket = fields.Char(sparse="data")
    aws_secret_key = fields.Char(sparse="data")
    aws_access_key = fields.Char(sparse="data")
    s3_public_base_url = fields.Char(sparse="data")

    def _amazon_s3store(self, vals):
        blob = vals['datas']
        checksum = u'' + hashlib.sha1(blob).hexdigest()

        name = vals.get('name', checksum)
        # todo add filename here (for extention)
        b_decoded = base64.b64decode(blob)
        try:
            with s3fs.S3FS(
                self.aws_bucket,
                aws_secret_key=self.aws_secret_key,
                aws_access_key=self.aws_access_key,
                host='s3.eu-central-1.amazonaws.com')
            ) as the_dir:
                the_dir.setcontents(name, b_decoded)
                size = the_dir.getsize(name)
        except socket.error:
            raise UserError('SFTP server not available')

        basic_vals = {
            'name': name,
            'url': name,
            'file_size': size,
            'checksum': checksum,
            'backend_id': self.id,
            'private_path': '' # todo here
        }
        return basic_vals

    def __amazon_s3get_public_url(self, obj):
        # TODO faire mieux
        logger.info('get_public_url')

        if obj.to_do:
            logger.warning(
                'public url not available for not processed thumbnail')
            return None
        return self.s3_public_base_url + obj.url

    def _amazon_s3get_base64(self, file_id):
        logger.info('return base64 of a file')
        with s3fs.S3FS(
            self.aws_bucket,
            aws_secret_key=self.aws_secret_key,
            aws_access_key=self.aws_access_key,
        ) as the_dir:
            return the_dir.open(file_id.url, 'r')
