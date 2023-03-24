# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# Copyright 2019 Camptocamp SA (http://www.camptocamp.com).
# @author Simone Orsi <simone.orsi@camptocamp.com>
# Copyright 2023 ACSONE SA/NV (http://acsone.eu).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
import functools
import inspect
import logging
import os.path
import re
import warnings
from typing import AnyStr, Callable, List

import fsspec

from odoo import _, api, fields, models
from odoo.exceptions import AccessError

from ..rooted_filesystem import RootedFileSystem

_logger = logging.getLogger(__name__)


# TODO: useful for the whole OCA?
def deprecated(reason):
    """Mark functions or classes as deprecated.

    Emit warning at execution.

    The @deprecated is used with a 'reason'.

        .. code-block:: python

            @deprecated("please, use another function")
            def old_function(x, y):
                pass
    """

    def decorator(func1):

        if inspect.isclass(func1):
            fmt1 = "Call to deprecated class {name} ({reason})."
        else:
            fmt1 = "Call to deprecated function {name} ({reason})."

        @functools.wraps(func1)
        def new_func1(*args, **kwargs):
            warnings.simplefilter("always", DeprecationWarning)
            warnings.warn(
                fmt1.format(name=func1.__name__, reason=reason),
                category=DeprecationWarning,
                stacklevel=2,
            )
            warnings.simplefilter("default", DeprecationWarning)
            return func1(*args, **kwargs)

        return new_func1

    return decorator


def _odoofs_path_validator(
    fs: fsspec.AbstractFileSystem, resolved_path: str, root_path: str
) -> None:
    if not resolved_path.startswith(root_path):
        raise AccessError(
            _("Access to %(resolved_path)s is forbidden", resolved_path=resolved_path)
        )


class StorageBackend(models.Model):
    _name = "storage.backend"
    _backend_name = "storage_backend"
    _description = "Storage Backend"

    __slots__ = ("_fs",)

    def __init__(self, env, ids=(), prefetch_ids=()):
        super().__init__(env, ids=ids, prefetch_ids=prefetch_ids)
        self._fs = None

    name = fields.Char(required=True)
    protocol = fields.Selection(
        selection="_get_protocols",
        required=True,
        default="odoofs",
        help="The protocol used to access the content of the storage backend.\n"
        "This list is the one supported by the fsspec library (see "
        "https://filesystem-spec.readthedocs.io/en/latest). A filesystem protocol"
        "is added by default and refers to the odoo local filesystem.\n"
        "Pay attention that according to the protocol, some storage_options must be"
        "provided through the storage_options field.",
    )
    storage_options = fields.Json(
        help="The storage options used to access the storage backend.\n"
        "This is a JSON field that depends on the protocol used.\n"
        "For example, for the sftp protocol, you can provide the following:\n"
        "{\n"
        "    'host': 'my.sftp.server',\n"
        "    'ssh_kwrags': {\n"
        "        'username': 'myuser',\n"
        "        'password': 'mypassword',\n"
        "        'port': 22,\n"
        "    }\n"
        "}\n"
        "For more information, please refer to the fsspec documentation:\n"
        "https://filesystem-spec.readthedocs.io/en/latest/api.html#built-in-implementations"
    )
    directory_path = fields.Char(
        help="Relative path to the directory to store the file"
    )

    def write(self, vals):
        self._fs = None
        return super().write(vals)

    @api.model
    def _get_protocols(self) -> List[tuple[str, str]]:
        protocol = [("odoofs", "Odoo's Filesystem")]
        for p in fsspec.available_protocols():
            try:
                cls = fsspec.get_filesystem_class(p)
                protocol.append((p, cls.__name__))
            except ImportError as e:
                _logger.debug("Cannot load the protocol %s. Reason: %s", p, e)
        return protocol

    @property
    def fs(self) -> fsspec.AbstractFileSystem:
        """Get the fsspec filesystem for this backend."""
        self.ensure_one()
        if not self._fs:
            self._fs = self._get_filesystem()
        return self._fs

    def _get_filesystem_storage_path(self) -> str:
        """Get the path to the storage directory.

        This path is relative to the odoo filestore.and is used as root path
        when the protocol is filesystem.
        """
        self.ensure_one()
        return os.path.join(self.env["ir.attachment"]._filestore(), "storage")

    def _get_path_validator(
        self,
    ) -> Callable[[fsspec.AbstractFileSystem, str, str], None] | None:
        """
        Get the function to validate the path.
        """
        self.ensure_one()
        if self.protocol == "odoofs":
            return _odoofs_path_validator
        return None

    def _get_rooted_filesystem(
        self, fs: fsspec.AbstractFileSystem, root_path
    ) -> fsspec.AbstractFileSystem:
        """Get the fsspec filesystem for this backend.

        This filesystem is rooted to the given path if provided.
        """
        self.ensure_one()
        path_validator = self._get_path_validator()
        return RootedFileSystem(fs, root_path, path_validator=path_validator)

    def _get_filesystem(self) -> fsspec.AbstractFileSystem:
        """Get the fsspec filesystem for this backend.

        See https://filesystem-spec.readthedocs.io/en/latest/api.html
        #fsspec.spec.AbstractFileSystem

        :return: fsspec.AbstractFileSystem
        """
        self.ensure_one()
        options = self.storage_options or {}
        protocol = self.protocol
        directory_path = self.directory_path
        if self.protocol == "odoofs":
            protocol = "dir"
            options["path"] = self._get_filesystem_storage_path()
        fs = fsspec.filesystem(protocol, **options)
        return self._get_rooted_filesystem(fs, directory_path)

    @deprecated("Please use _get_filesystem() instead and the fsspec API directly.")
    def add(self, relative_path, data, binary=True, **kwargs) -> None:
        if not binary:
            data = base64.b64decode(data)
        path = relative_path.split(self.fs.sep)[:-1]
        if not self.fs.exists(self.fs.sep.join(path)):
            self.fs.makedirs(self.fs.sep.join(path))
        with self.fs.open(relative_path, "wb", **kwargs) as f:
            f.write(data)

    @deprecated("Please use _get_filesystem() instead and the fsspec API directly.")
    def get(self, relative_path, binary=True, **kwargs) -> AnyStr:
        data = self.fs.read_bytes(relative_path, **kwargs)
        if not binary and data:
            data = base64.b64encode(data)
        return data

    @deprecated("Please use _get_filesystem() instead and the fsspec API directly.")
    def list_files(self, relative_path="", pattern=False) -> List[str]:
        relative_path = relative_path or self.fs.root_marker
        if not self.fs.exists(relative_path):
            return []
        if pattern:
            relative_path = self.fs.sep.join([relative_path, pattern])
            return self.fs.glob(relative_path)
        return self.fs.ls(relative_path, detail=False)

    @deprecated("Please use _get_filesystem() instead and the fsspec API directly.")
    def find_files(self, pattern, relative_path="", **kw) -> List[str]:
        """Find files matching given pattern.

        :param pattern: regex expression
        :param relative_path: optional relative path containing files
        :return: list of file paths as full paths from the root
        """
        result = []
        relative_path = relative_path or self.fs.root_marker
        if not self.fs.exists(relative_path):
            return []
        regex = re.compile(pattern)
        for file_path in self.fs.ls(relative_path, detail=False):
            if regex.match(file_path):
                result.append(file_path)
        return result

    @deprecated("Please use _get_filesystem() instead and the fsspec API directly.")
    def move_files(self, files, destination_path, **kw) -> None:
        """Move files to given destination.

        :param files: list of file paths to be moved
        :param destination_path: directory path where to move files
        :return: None
        """
        for file_path in files:
            self.fs.move(
                file_path,
                self.fs.sep.join([destination_path, os.path.basename(file_path)]),
                **kw
            )

    @deprecated("Please use _get_filesystem() instead and the fsspec API directly.")
    def delete(self, relative_path) -> None:
        self.fs.rm_file(relative_path)

    def action_test_config(self) -> None:
        try:
            self.fs.ls("", detail=False)
            title = _("Connection Test Succeeded!")
            message = _("Everything seems properly set up!")
            msg_type = "success"
        except Exception as err:
            title = _("Connection Test Failed!")
            message = str(err)
            msg_type = "danger"
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": title,
                "message": message,
                "type": msg_type,
                "sticky": False,
            },
        }
