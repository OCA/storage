# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import socket
import hashlib
import logging
import base64

from openerp import fields, models
from openerp.exceptions import Warning as UserError

logger = logging.getLogger(__name__)

try:
    from fs import sftpfs
except ImportError as err:
    logger.debug(err)


class SftpStorageBackend(models.Model):
    _inherit = 'storage.backend'

    sftp_public_base_url = fields.Char(
        string='Public url',
        help='')
    sftp_server = fields.Char(
        string='SFTP host',
        help='')
    sftp_dir_path = fields.Char(
        string='Remote path',
        help='Dir on the server where to store files')

    # TODO externiser ça dans des parametres
    # ou dans un keychain ?

    def _sftpstore(self, vals):
        blob = vals['datas']
        checksum = u'' + hashlib.sha1(blob).hexdigest()

        name = vals.get('name', checksum)
        # todo add filename here (for extention)
        b_decoded = base64.b64decode(blob)
        try:
            with sftpfs.SFTPFS(
                self.sftp_server,
                root_path=self.sftp_dir_path
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
            'private_path': self.sftp_dir_path + name,
        }
        return basic_vals

    def _sftpget_public_url(self, obj):
        # TODO faire mieux
        logger.info('get_public_url')

        if obj.to_do:
            logger.warning(
                'public url not available for not processed thumbnail')
            return None
        return self.sftp_public_base_url + obj.url

    def _sftpget_base64(self, file_id):
        logger.info('return base64 of a file')
        with sftpfs.SFTPFS(
            self.sftp_server,
            root_path=self.sftp_dir_path
        ) as the_dir:
            return the_dir.open(file_id.url, 'r')
