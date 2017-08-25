# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import socket
import logging
import base64
import os

from openerp import fields, models
from openerp.exceptions import Warning as UserError
from openerp.tools.translate import _

logger = logging.getLogger(__name__)

try:
    from fs import sftpfs
except ImportError as err:
    logger.debug(err)


class SftpStorageBackend(models.Model):
    _inherit = 'storage.backend'

    backend_type = fields.Selection(
        selection_add=[('sftp', 'SFTP')])

    sftp_public_base_url = fields.Char(
        string='Public url',
        help='',
        sparse="data"
    )
    sftp_server = fields.Char(
        string='SFTP host',
        help='Can include the port if necessary, like '
             'my-server:22222',
        sparse="data"
    )
    sftp_dir_path = fields.Char(
        string='Remote path',
        help='Dir on the server where to store files',
        sparse="data"
    )
    sftp_login = fields.Char(
        string='SFTP login',
        help='Login to connect to sftp server',
        sparse="data"
    )

    # TODO externiser ça dans des parametres
    # ou dans un keychain ?
    # Can't work without login/password??
#    def _sftp_store(self, name, datas, is_public=False):
#        checksum = u'' + hashlib.sha1(blob).hexdigest()
#        name = name or checksum
#        # todo add filename here (for extention)
#        b_decoded = base64.b64decode(datas)
#        try:
#            with sftpfs.SFTPFS(
#                self.sftp_server,
#                root_path=self.sftp_dir_path
#            ) as the_dir:
#                the_dir.setcontents(name, b_decoded)
#        except socket.error:
#            raise UserError('SFTP server not available')
#        return name

    def _sftp_store(self, name, datas, is_public=False):
        # todo add filename here (for extention)
        try:
            account = self._get_keychain_account()
            password = account.get_password()
            with sftpfs.SFTPFS(connection=self.sftp_server,
                               username=self.sftp_login,
                               password=password
                               ) as conn:
                full_path = os.path.join(self.sftp_dir_path, name)
                conn.setcontents(full_path, datas)
        except socket.error:
            raise UserError(_('SFTP server not available'))
        return name

    def _sftpget_public_url(self, name):
        # TODO faire mieux
        logger.info('get_public_url')

        host = self.sftp_public_base_url
        directory = self.sftp_dir_path
        return "https://%s/%s/%s" % (host, directory, name)

    def _sftpretrieve_datas(self, name):
        logger.info('return base64 of a file')
        try:
            account = self._get_keychain_account()
            password = account.get_password()
            with sftpfs.SFTPFS(connection=self.sftp_server,
                               username=self.sftp_login,
                               password=password
                               ) as conn:
                full_path = os.path.join(self.sftp_dir_path, name)
                file_data = conn.open(full_path, 'rb')
                datas = file_data.read()
                datas_encoded = datas and base64.b64encode(datas) or False
        except socket.error:
            raise UserError(_('SFTP server not available'))
        return datas_encoded
