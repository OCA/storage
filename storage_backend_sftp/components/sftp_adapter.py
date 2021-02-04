# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# Copyright 2019 Camptocamp SA (http://www.camptocamp.com).
# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import errno
import logging
import os
from contextlib import contextmanager
from io import StringIO

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)

try:
    import paramiko
except ImportError as err:  # pragma: no cover
    _logger.debug(err)


def sftp_mkdirs(client, path, mode=511):
    try:
        client.mkdir(path, mode)
    except IOError as e:
        if e.errno == errno.ENOENT and path:
            sftp_mkdirs(client, os.path.dirname(path), mode=mode)
            client.mkdir(path, mode)
        else:
            raise  # pragma: no cover


def load_ssh_key(ssh_key_buffer):
    for pkey_class in (
        paramiko.RSAKey,
        paramiko.DSSKey,
        paramiko.ECDSAKey,
        paramiko.Ed25519Key,
    ):
        try:
            return pkey_class.from_private_key(ssh_key_buffer)
        except paramiko.SSHException:
            ssh_key_buffer.seek(0)  # reset the buffer "file"
    raise Exception("Invalid ssh private key")


@contextmanager
def sftp(backend):
    transport = paramiko.Transport((backend.sftp_server, backend.sftp_port))
    if backend.sftp_auth_method == "pwd":
        transport.connect(username=backend.sftp_login, password=backend.sftp_password)
    elif backend.sftp_auth_method == "ssh_key":
        ssh_key_buffer = StringIO(backend.sftp_ssh_private_key)
        private_key = load_ssh_key(ssh_key_buffer)
        transport.connect(username=backend.sftp_login, pkey=private_key)
    client = paramiko.SFTPClient.from_transport(transport)
    yield client
    transport.close()


class SFTPStorageBackendAdapter(Component):
    _name = "sftp.adapter"
    _inherit = "base.storage.adapter"
    _usage = "sftp"

    def add(self, relative_path, data, **kwargs):
        with sftp(self.collection) as client:
            full_path = self._fullpath(relative_path)
            dirname = os.path.dirname(full_path)
            if dirname:
                try:
                    client.stat(dirname)
                except IOError as e:
                    if e.errno == errno.ENOENT:
                        sftp_mkdirs(client, dirname)
                    else:
                        raise  # pragma: no cover
            remote_file = client.open(full_path, "w+b")
            remote_file.write(data)
            remote_file.close()

    def get(self, relative_path, **kwargs):
        full_path = self._fullpath(relative_path)
        with sftp(self.collection) as client:
            file_data = client.open(full_path, "rb")
            data = file_data.read()
            # TODO: shouldn't we close the file?
        return data

    def list(self, relative_path):
        full_path = self._fullpath(relative_path)
        with sftp(self.collection) as client:
            try:
                return client.listdir(full_path)
            except IOError as e:
                if e.errno == errno.ENOENT:
                    # The path do not exist return an empty list
                    return []
                else:
                    raise  # pragma: no cover

    def move_files(self, files, destination_path):
        _logger.debug("mv %s %s", files, destination_path)
        with sftp(self.collection) as client:
            for sftp_file in files:
                dest_file_path = os.path.join(
                    destination_path, os.path.basename(sftp_file)
                )
                # Remove existing file at the destination path (an error is raised
                # otherwise)
                try:
                    client.lstat(dest_file_path)
                except FileNotFoundError:
                    _logger.debug("destination %s is free", dest_file_path)
                else:
                    client.unlink(dest_file_path)
                # Move the file
                client.rename(sftp_file, dest_file_path)

    def delete(self, relative_path):
        full_path = self._fullpath(relative_path)
        with sftp(self.collection) as client:
            return client.remove(full_path)

    def validate_config(self):
        with sftp(self.collection) as client:
            client.listdir()
