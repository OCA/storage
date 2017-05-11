# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import socket
import hashlib
import logging
import base64
import mimetypes

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

    def _amazon_s3store(self, vals):
        blob = vals['datas']
        checksum = u'' + hashlib.sha1(blob).hexdigest()

        name = vals.get('name', checksum)
        # todo add filename here (for extention)
        mime, enc = mimetypes.guess_type(name)

        b_decoded = base64.b64decode(blob)
        try:
            with s3fs.S3FS(
                self.aws_bucket,
                aws_secret_key=self.aws_secret_key,
                aws_access_key=self.aws_access_key,
                host='s3.eu-central-1.amazonaws.com'
            ) as the_dir:
                the_dir.setcontents(name, b_decoded)
                size = the_dir.getsize(name)
                url = the_dir.getpathurl(name)
                # Todo : j'arrive pas mettre le mime type ici
                key = the_dir._s3bukt.get_key(name)
                key.copy(
                    key.bucket,
                    key.name,
                    preserve_acl=True,
                    metadata={'Content-Type': mime})
        except socket.error:
            raise UserError('S3 server not available')

        basic_vals = {
            'name': name,
            'url': url,
            'file_size': size,
            'checksum': checksum,
            'backend_id': self.id,
            'private_path': name
        }
        return basic_vals

    def _amazon_s3get_public_url(self, obj):
        # TODO faire mieux
        logger.info('get_public_url')
        return obj.url

    def _amazon_s3get_base64(self, file_id):
        logger.warning('return base64 of a file')
        with s3fs.S3FS(
            self.aws_bucket,
            aws_secret_key=self.aws_secret_key,
            aws_access_key=self.aws_access_key,
            host='s3.eu-central-1.amazonaws.com'
        ) as the_dir:
            # TODO : quel horreur ! on a deja l'url
            bin = the_dir.getcontents(file_id.name)  # mettre private_path
            return base64.b64encode(bin)
