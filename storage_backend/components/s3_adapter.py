# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import socket
import logging
import mimetypes
import base64

from odoo import models
from odoo.exceptions import UserError
from odoo.tools.translate import _


logger = logging.getLogger(__name__)

try:
    from boto.s3.connection import S3Connection
except ImportError as err:
    logger.debug(err)


class S3StorageBackend(models.Model):
    _inherit = 'storage.backend'

    def _amazon_s3_store_data(self, name, datas, is_public=False):
        mime, enc = mimetypes.guess_type(name)
        account = self._get_existing_keychain()
        try:
            conn = S3Connection(
                self.aws_access_key,
                account._get_password(),
                host=self.aws_host)
            buck = conn.get_bucket(self.aws_bucket)
            if self.aws_directory:
                name = "%s/%s" % (self.aws_directory, name)
            key = buck.get_key(name)
            if not key:
                key = buck.new_key(name)
            key.set_metadata("Content-Type", mime)
            key.set_contents_from_string(datas)
            if is_public:
                key.make_public()
        except socket.error:
            raise UserError(_('S3 server not available'))
        return name

    def _amazon_s3_get_public_url(self, path):
        if self.aws_cloudfront_domain:
            if self.aws_cloudfront_domain_include_directory:
                if path.startswith('%s/' % self.aws_directory):
                    path = path[len(self.aws_directory) + 1:]
                else:
                    raise UserError(_('Path do not match with aws directory'))
            return "https://%s/%s" % (self.aws_cloudfront_domain, path)
        else:
            return "https://%s/%s/%s" % (self.aws_host, self.aws_bucket, path)

    def _amazon_s3_retrieve_data(self, name):
        logger.debug('Backend Storage: Read file %s from amazon S3', name)
        account = self._get_existing_keychain()
        try:
            conn = S3Connection(
                self.aws_access_key,
                account._get_password(),
                host=self.aws_host)
            buck = conn.get_bucket(self.aws_bucket)
            key = buck.get_key(name)
            datas = key.read()
        except socket.error:
            raise UserError(_('S3 server not available'))
        return datas and base64.b64encode(datas) or False
