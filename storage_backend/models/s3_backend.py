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
    from boto.s3.connection import S3Connection
except ImportError as err:
    logger.debug(err)


class S3StorageBackend(models.Model):
    _inherit = 'storage.backend'

    backend_type = fields.Selection(
        selection_add=[('amazon_s3', 'Amazon S3')])

    aws_bucket = fields.Char(sparse="data")
    aws_secret_key = fields.Char(sparse="data")
    aws_access_key = fields.Char(sparse="data")
    aws_host = fields.Char(sparse="data")
    aws_cloudfront_domain = fields.Char(sparse="data")

    def _amazon_s3_build_public_url(self, name):
        if self.aws_cloudfront_domain:
            host = self.aws_cloutfront_domain
        else:
            host = self.aws_host
        return "https://%s/%s/%s" % (host, self.aws_bucket, name)

    def _amazon_s3store(self, vals):
        name = vals['name']
        mime, enc = mimetypes.guess_type(name)
        b_decoded = base64.b64decode(vals['datas'])
        try:
            conn = S3Connection(
                self.aws_access_key,
                self.aws_secret_key,
                host=self.aws_host)
            buck = conn.get_bucket('storage-testing-raph')
            key = buck.get_key(name)
            if not key:
                key = buck.new_key(name)
            key.set_metadata("Content-Type", mime)
            key.set_contents_from_string(b_decoded)
            key.make_public()
        except socket.error:
            raise UserError('S3 server not available')

        return {
            'name': name,
            'url': self._amazon_s3_build_public_url(name),
            'file_size': key.size,
            'checksum': key.md5,
            'backend_id': self.id,
            'private_path': name
        }

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
