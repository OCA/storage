# Copyright 2023 ACSONE SA/NV (https://www.acsone.eu).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from __future__ import annotations

import base64
import functools
import inspect
import io
import json
import logging
import os.path
import re
import warnings
from typing import AnyStr

import fsspec

from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError

from odoo.addons.base_sparse_field.models.fields import Serialized

_logger = logging.getLogger(__name__)

try:
    import paramiko

    SSH_PKEYS = {
        "DSS": paramiko.DSSKey,
        "RSA": paramiko.RSAKey,
        "EC": paramiko.ECDSAKey,
        "OPENSSH": paramiko.Ed25519Key,
    }
except ImportError:  # pragma: no cover
    _logger.debug("Cannot `import paramiko`.")
    SSH_PKEYS = {}


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


class FSStorage(models.Model):
    _name = "fs.storage"
    _inherit = "server.env.mixin"
    _description = "FS Storage"

    __slots__ = ("__fs", "__odoo_storage_path")

    def __init__(self, env, ids=(), prefetch_ids=()):
        super().__init__(env, ids=ids, prefetch_ids=prefetch_ids)
        self.__fs = None
        self.__odoo_storage_path = None

    name = fields.Char(required=True)
    code = fields.Char(
        required=True,
        help="Technical code used to identify the storage backend into the code."
        "This code must be unique. This code is used for example to define the "
        "storage backend to store the attachments via the configuration parameter "
        "'ir_attachment.storage.force.database' when the module 'fs_attachment' "
        "is installed.",
    )
    protocol = fields.Selection(
        selection="_get_protocols",
        required=True,
        default="odoofs",
        help="The protocol used to access the content of filesystem.\n"
        "This list is the one supported by the fsspec library (see "
        "https://filesystem-spec.readthedocs.io/en/latest). A filesystem protocol"
        "is added by default and refers to the odoo local filesystem.\n"
        "Pay attention that according to the protocol, some options must be"
        "provided through the options field.",
    )
    protocol_descr = fields.Text(
        compute="_compute_protocol_descr",
    )
    options = fields.Text(
        help="The options used to initialize the filesystem.\n"
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

    json_options = Serialized(
        help="The options used to initialize the filesystem.\n",
        compute="_compute_json_options",
        inverse="_inverse_json_options",
    )

    eval_options_from_env = fields.Boolean(
        string="Resolve env vars",
        help="""Resolve options values starting with $ from environment variables. e.g
            {
                "endpoint_url": "$AWS_ENDPOINT_URL",
            }
            """,
    )

    directory_path = fields.Char(
        help="Relative path to the directory to store the file"
    )

    # the next fields are used to display documentation to help the user
    # to configure the backend
    options_protocol = fields.Selection(
        string="Describes Protocol",
        selection="_get_options_protocol",
        compute="_compute_protocol_descr",
        help="The protocol used to access the content of filesystem.\n"
        "This list is the one supported by the fsspec library (see "
        "https://filesystem-spec.readthedocs.io/en/latest). A filesystem protocol"
        "is added by default and refers to the odoo local filesystem.\n"
        "Pay attention that according to the protocol, some options must be"
        "provided through the options field.",
    )
    options_properties = fields.Text(
        string="Available properties",
        compute="_compute_options_properties",
        store=False,
    )

    _sql_constraints = [
        (
            "code_uniq",
            "unique(code)",
            "The code must be unique",
        ),
    ]

    _server_env_section_name_field = "code"

    @property
    def _server_env_fields(self):
        return {"protocol": {}, "options": {}, "directory_path": {}}

    def write(self, vals):
        self.__fs = None
        self.clear_caches()
        return super().write(vals)

    @api.model
    @tools.ormcache()
    def get_id_by_code_map(self):
        """Return a dictionary with the code as key and the id as value."""
        return {rec.code: rec.id for rec in self.sudo().search([])}

    @api.model
    def get_id_by_code(self, code):
        """Return the id of the filesystem associated to the given code."""
        return self.get_id_by_code_map().get(code)

    @api.model
    def get_by_code(self, code) -> FSStorage:
        """Return the filesystem associated to the given code."""
        res = self.browse()
        res_id = self.get_id_by_code(code)
        if res_id:
            res = self.browse(res_id)
        return res

    @api.model
    @tools.ormcache()
    def get_storage_codes(self):
        """Return the list of codes of the existing filesystems."""
        return [s.code for s in self.search([])]

    @api.model
    @tools.ormcache("code")
    def get_fs_by_code(self, code):
        """Return the filesystem associated to the given code.

        :param code: the code of the filesystem
        """
        fs = None
        fs_storage = self.get_by_code(code)
        if fs_storage:
            fs = fs_storage.fs
        return fs

    def copy(self, default=None):
        default = default or {}
        if "code" not in default:
            default["code"] = "{}_copy".format(self.code)
        return super().copy(default)

    @api.model
    def _get_protocols(self) -> list[tuple[str, str]]:
        protocol = [("odoofs", "Odoo's FileSystem")]
        for p in fsspec.available_protocols():
            try:
                cls = fsspec.get_filesystem_class(p)
                protocol.append((p, f"{p} ({cls.__name__})"))
            except ImportError as e:
                _logger.debug("Cannot load the protocol %s. Reason: %s", p, e)
        return protocol

    @api.constrains("options")
    def _check_options(self) -> None:
        for rec in self:
            try:
                json.loads(rec.options or "{}")
            except Exception as e:
                raise ValidationError(_("The options must be a valid JSON")) from e

    @api.depends("options")
    def _compute_json_options(self) -> None:
        for rec in self:
            rec.json_options = json.loads(rec.options or "{}")

    def _inverse_json_options(self) -> None:
        for rec in self:
            rec.options = json.dumps(rec.json_options)

    @api.depends("protocol")
    def _compute_protocol_descr(self) -> None:
        for rec in self:
            rec.protocol_descr = fsspec.get_filesystem_class(rec.protocol).__doc__
            rec.options_protocol = rec.protocol

    @api.model
    def _get_options_protocol(self) -> list[tuple[str, str]]:
        protocol = [("odoofs", "Odoo's Filesystem")]
        for p in fsspec.available_protocols():
            try:
                fsspec.get_filesystem_class(p)
                protocol.append((p, p))
            except ImportError as e:
                _logger.debug("Cannot load the protocol %s. Reason: %s", p, e)
        return protocol

    @api.depends("options_protocol")
    def _compute_options_properties(self) -> None:
        for rec in self:
            cls = fsspec.get_filesystem_class(rec.options_protocol)
            signature = inspect.signature(cls.__init__)
            doc = inspect.getdoc(cls.__init__)
            rec.options_properties = f"__init__{signature}\n{doc}"

    @property
    def fs(self) -> fsspec.AbstractFileSystem:
        """Get the fsspec filesystem for this backend."""
        self.ensure_one()
        if not self.__fs:
            self.__fs = self._get_filesystem()
        return self.__fs

    def _get_filesystem_storage_path(self) -> str:
        """Get the path to the storage directory.

        This path is relative to the odoo filestore.and is used as root path
        when the protocol is filesystem.
        """
        self.ensure_one()
        path = os.path.join(self.env["ir.attachment"]._filestore(), "storage")
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    @property
    def _odoo_storage_path(self) -> str:
        """Get the path to the storage directory.

        This path is relative to the odoo filestore.and is used as root path
        when the protocol is filesystem.
        """
        if not self.__odoo_storage_path:
            self.__odoo_storage_path = self._get_filesystem_storage_path()
        return self.__odoo_storage_path

    def _recursive_add_odoo_storage_path(self, options: dict) -> dict:
        """Add the odoo storage path to the options.

        This is a recursive function that will add the odoo_storage_path
        option to the nested target_options if the target_protocol is
        odoofs
        """
        if "target_protocol" in options:
            target_options = options.get("target_options", {})
            if options["target_protocol"] == "odoofs":
                target_options["odoo_storage_path"] = self._odoo_storage_path
                options["target_options"] = target_options
            self._recursive_add_odoo_storage_path(target_options)
        return options

    def _eval_options_from_env(self, options):
        values = {}
        for key, value in options.items():
            if isinstance(value, dict):
                values[key] = self._eval_options_from_env(value)
            elif isinstance(value, str) and value.startswith("$"):
                env_variable_name = value[1:]
                env_variable_value = os.getenv(env_variable_name)
                if env_variable_value is not None:
                    values[key] = env_variable_value
                else:
                    values[key] = value
                    _logger.warning(
                        "Environment variable %s is not set for fs_storage %s.",
                        env_variable_name,
                        self.display_name,
                    )
            else:
                values[key] = value
        return values

    def _get_fs_options(self):
        options = self.json_options
        if not self.eval_options_from_env:
            return options
        return self._eval_options_from_env(self.json_options)

    def _get_filesystem(self) -> fsspec.AbstractFileSystem:
        """Get the fsspec filesystem for this backend.

        See https://filesystem-spec.readthedocs.io/en/latest/api.html
        #fsspec.spec.AbstractFileSystem

        :return: fsspec.AbstractFileSystem
        """
        self.ensure_one()
        options = self._get_fs_options()
        if self.protocol == "odoofs":
            options["odoo_storage_path"] = self._odoo_storage_path
        # Webdav protocol handler does need the auth to be a tuple not a list !
        if (
            self.protocol == "webdav"
            and "auth" in options
            and isinstance(options["auth"], list)
        ):
            options["auth"] = tuple(options["auth"])
        if (
            self.protocol in ("sftp", "ssh")
            and "pkey" in options
            and isinstance(options["pkey"], str)
        ):
            # Handle SSH private keys by replacing 'pkey' parameter by a
            # paramiko.pkey.PKey object
            pkey_file = io.StringIO(options["pkey"])
            pkey = self._get_ssh_private_key(
                pkey_file,
                passphrase=options.get("passphrase"),
            )
            options["pkey"] = pkey
        options = self._recursive_add_odoo_storage_path(options)
        fs = fsspec.filesystem(self.protocol, **options)
        directory_path = self.directory_path
        if directory_path:
            fs = fsspec.filesystem("rooted_dir", path=directory_path, fs=fs)
        return fs

    def _detect_ssh_private_key_type(self, pkey_file):
        """Detect SSH private key type (RSA, DSS...)."""
        # Code copied and adapted from 'paramiko.pkey.PKey._read_private_key' method
        # https://github.com/paramiko/paramiko/blob/main/paramiko/pkey.py#L498C9-L498C26
        pkey_file.seek(0)
        lines = pkey_file.readlines()
        pkey_file.seek(0)
        if not lines:
            raise paramiko.SSHException("no lines in private key file")
        start = 0
        m = paramiko.pkey.PKey.BEGIN_TAG.match(lines[start])
        line_range = len(lines) - 1
        while start < line_range and not m:
            start += 1
            m = paramiko.pkey.PKey.BEGIN_TAG.match(lines[start])
        start += 1
        keytype = m.group(1) if m else None
        if keytype:
            return keytype

    def _get_ssh_private_key(self, pkey_file, passphrase=None):
        """Build the expected `paramiko.pkey.PKey` object."""
        pkey_type = self._detect_ssh_private_key_type(pkey_file)
        if not pkey_type:
            raise paramiko.SSHException("not a valid private key file")
        return SSH_PKEYS[pkey_type].from_private_key(pkey_file, password=passphrase)

    # Deprecated methods used to ease the migration from the storage_backend addons
    # to the fs_storage addons. These methods will be removed in the future (Odoo 18)
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
    def list_files(self, relative_path="", pattern=False) -> list[str]:
        relative_path = relative_path or self.fs.root_marker
        if not self.fs.exists(relative_path):
            return []
        if pattern:
            relative_path = self.fs.sep.join([relative_path, pattern])
            return self.fs.glob(relative_path)
        return self.fs.ls(relative_path, detail=False)

    @deprecated("Please use _get_filesystem() instead and the fsspec API directly.")
    def find_files(self, pattern, relative_path="", **kw) -> list[str]:
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
                **kw,
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
