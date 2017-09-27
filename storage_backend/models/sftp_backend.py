# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import base64
import os
import errno

from openerp import fields, models
from contextlib import contextmanager

logger = logging.getLogger(__name__)

try:
    import paramiko
except ImportError as err:
    logger.debug(err)


def sftp_mkdirs(client, path, mode=511):
    try:
        client.mkdir(path, mode)
    except IOError, e:
        if e.errno == errno.ENOENT:
            sftp_mkdirs(client, os.path.dirname(path), mode=mode)
            client.mkdir(path, mode)
        else:
            raise


@contextmanager
def sftp(backend):
    account = backend._get_keychain_account()
    password = account.get_password()
    transport = paramiko.Transport((backend.sftp_server, backend.sftp_port))
    transport.connect(username=backend.sftp_login, password=password)
    client = paramiko.SFTPClient.from_transport(transport)
    yield client
    transport.close()


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
        sparse="data"
    )
    sftp_port = fields.Integer(
        string='SFTP port',
        default=22,
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

    def _sftp_store_data(self, name, datas, is_public=False):
        with sftp(self) as client:
            full_path = os.path.join(self.sftp_dir_path or '/', name)
            dirname = os.path.dirname(full_path)
            try:
                client.stat(dirname)
            except IOError, e:
                if e.errno == errno.ENOENT:
                    sftp_mkdirs(client, dirname)
                else:
                    raise
            logger.debug(
                'Backend Storage: Write file %s to filestore', full_path)
            remote_file = client.open(full_path, 'w+b')
            remote_file.write(datas)
            remote_file.close()
        return name

    def _sftp_get_public_url(self, name):
        return os.path.join(self.sftp_public_base_url, name)

    def _sftp_retrieve_datas(self, name):
        logger.debug('Backend Storage: Read file %s from filestore', name)
        full_path = os.path.join(self.sftp_dir_path or '/', name)
        with sftp(self) as client:
            file_data = client.open(full_path, 'rb')
            datas = file_data.read()
            datas_encoded = datas and base64.b64encode(datas) or False
        return datas_encoded
