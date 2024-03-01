# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# Copyright 2019 Camptocamp SA (http://www.camptocamp.com).
# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import errno
import logging
import os
import re
from contextlib import contextmanager
from io import StringIO
from stat import S_ISDIR, S_ISREG

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
            remote_file = client.open(full_path, "w")
            remote_file.write(data)
            remote_file.close()

    def get(self, relative_path, **kwargs):
        full_path = self._fullpath(relative_path)
        with sftp(self.collection) as client:
            file_data = client.open(full_path, "r")
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

    def find_files(self, pattern, relative_path="", **kwargs):
        """Find files matching given pattern.

        :param pattern: regex expression
        :param relative_path: optional relative path containing files
        :keyword include_regular_files: include regular files in the result
        :keyword include_folders: include folders in the result
        :keyword include_other_files: include other files in the result
        :return: list of file paths as full paths from the root
        """
        regex = re.compile(pattern)

        include_regular_files = kwargs.get("include_regular_files", True)
        include_folders = kwargs.get("include_folders", True)
        include_other_files = kwargs.get("include_other_files", True)

        full_path = self._fullpath(relative_path)
        filelist = []
        with sftp(self.collection) as client:
            file_attrs = client.listdir_attr(full_path)

            for entry in file_attrs:
                mode = entry.st_mode
                if S_ISDIR(mode) and include_folders:
                    filelist.append(entry.filename)
                elif S_ISREG(mode) and include_regular_files:
                    filelist.append(entry.filename)
                elif include_other_files:
                    filelist.append(entry.filename)

        files_matching = [
            regex.match(file_).group() for file_ in filelist if regex.match(file_)
        ]
        return files_matching

    def move_files(self, files, destination_path):
        _logger.debug("mv %s %s", files, destination_path)
        destination_full_path = self._fullpath(destination_path)
        with sftp(self.collection) as client:
            for sftp_file in files:
                dest_file_path = os.path.join(
                    destination_full_path, os.path.basename(sftp_file)
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
                full_path = self._fullpath(sftp_file)
                client.rename(full_path, dest_file_path)

    def delete(self, relative_path):
        full_path = self._fullpath(relative_path)
        with sftp(self.collection) as client:
            return client.remove(full_path)

    def validate_config(self):
        with sftp(self.collection) as client:
            client.listdir()
