# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# Copyright 2019 Camptocamp SA (http://www.camptocamp.com).
# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
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
    _logger.debug("Paramiko not installed: %s", err)


def sftp_mkdirs(client, path, mode=0o777):
    """Recursively create directories on the SFTP server."""
    try:
        client.mkdir(path, mode)
    except IOError as e:
        if e.errno == errno.ENOENT and path:
            sftp_mkdirs(client, os.path.dirname(path), mode=mode)
            client.mkdir(path, mode)
        else:
            raise


def load_ssh_key(ssh_key_buffer):
    """Load SSH key from buffer and return the key object."""
    for pkey_class in (
        paramiko.RSAKey,
        paramiko.DSSKey,
        paramiko.ECDSAKey,
        paramiko.Ed25519Key,
    ):
        try:
            return pkey_class.from_private_key(ssh_key_buffer)
        except paramiko.SSHException as err:
            ssh_key_buffer.seek(0)  # Reset buffer
            raise ValueError("Invalid SSH private key provided") from err


@contextmanager
def sftp(backend):
    """SFTP connection manager ensuring proper closure."""
    transport = paramiko.Transport((backend.sftp_server, backend.sftp_port))
    try:
        if backend.sftp_auth_method == "pwd":
            transport.connect(
                username=backend.sftp_login, password=backend.sftp_password
            )
        elif backend.sftp_auth_method == "ssh_key":
            (ssh_key_buffer) = StringIO(backend.sftp_ssh_private_key)
            private_key = load_ssh_key(ssh_key_buffer)
            transport.connect(username=backend.sftp_login, pkey=private_key)
        client = paramiko.SFTPClient.from_transport(transport)
        yield client
    finally:
        try:
            client.close()
        except Exception:
            _logger.warning("Failed to close SFTP client")
        try:
            transport.close()
        except Exception:
            _logger.warning("Failed to close SFTP transport")


class SFTPStorageBackendAdapter(Component):
    _name = "sftp.adapter"
    _inherit = "base.storage.adapter"
    _usage = "sftp"

    def add(self, relative_path, data, **kwargs):
        """Upload a file to the SFTP server."""
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
                        raise
            with client.open(full_path, "w+b") as remote_file:
                remote_file.write(data)

    def get(self, relative_path, **kwargs):
        full_path = self._fullpath(relative_path)
        with sftp(self.collection) as client:
            with client.open(full_path, "rb") as file_data:
                return file_data.read()

    def list(self, relative_path):
        """List files in the specified directory on the SFTP server."""
        full_path = self._fullpath(relative_path)
        with sftp(self.collection) as client:
            try:
                return client.listdir(full_path)
            except IOError as e:
                if e.errno == errno.ENOENT:
                    return []  # Directory does not exist
                raise

    def move_files(self, files, destination_path):
        """Move files to a new location on the SFTP server."""
        _logger.debug("Moving files: %s -> %s", files, destination_path)
        fp = self._fullpath
        with sftp(self.collection) as client:
            for sftp_file in files:
                dest_file_path = os.path.join(
                    destination_path, os.path.basename(sftp_file)
                )
                try:
                    client.lstat(dest_file_path)
                    client.unlink(dest_file_path)
                except FileNotFoundError:
                    _logger.debug("Destination %s is available", dest_file_path)
                client.rename(fp(sftp_file), fp(dest_file_path))

    def delete(self, relative_path):
        """Delete a file from the SFTP server."""
        full_path = self._fullpath(relative_path)
        with sftp(self.collection) as client:
            client.remove(full_path)

    def validate_config(self):
        """Validate the SFTP connection by listing files in the root directory."""
        with sftp(self.collection) as client:
            client.listdir("/")
