# Copyright 2017-2013 Camptocamp SA
# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from __future__ import annotations

import hashlib
import io
import logging
import mimetypes
import os
import re
import shutil
import time
from contextlib import closing, contextmanager
from pathlib import Path

import fsspec
import psycopg2
from slugify import slugify

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.fields import Domain
from odoo.modules.registry import Registry
from odoo.tools.binary import BinaryValue

from odoo.addons.base.models.ir_attachment import (
    CREATE_FROM_STREAM_FLAG,
)
from odoo.addons.base.models.ir_attachment import (
    IrAttachment as BaseIrAttachment,
)

from ..fs_stream import FsStream
from .strtobool import strtobool

_logger = logging.getLogger(__name__)


REGEX_SLUGIFY = r"[^-a-z0-9_]+"

FS_FILENAME_RE_PARSER = re.compile(
    r"^(?P<name>.+)-(?P<id>\d+)-(?P<version>\d+)(?P<extension>\..+)$"
)


def is_true(strval):
    return bool(strtobool(strval or "0"))


def clean_fs(files):
    _logger.info("cleaning old files from filestore")
    for full_path in files:
        if os.path.exists(full_path):
            try:
                os.unlink(full_path)
            except OSError:
                _logger.info(
                    "_file_delete could not unlink %s", full_path, exc_info=True
                )


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    fs_filename = fields.Char(
        "File Name into the filesystem storage",
        help="The name of the file in the filesystem storage."
        "To preserve the mimetype and the meaning of the filename"
        "the filename is computed from the name and the extension",
        readonly=True,
    )

    internal_url = fields.Char(
        "Internal URL",
        compute="_compute_internal_url",
        help="The URL to access the file from the server.",
    )

    fs_url = fields.Char(
        "Filesystem URL",
        compute="_compute_fs_url",
        help="The URL to access the file from the filesystem storage.",
        store=True,
    )
    fs_url_path = fields.Char(
        "Filesystem URL Path",
        compute="_compute_fs_url_path",
        help="The path to access the file from the filesystem storage.",
    )
    fs_storage_code = fields.Char(
        "Filesystem Storage Code",
        related="fs_storage_id.code",
        store=True,
    )
    fs_storage_id = fields.Many2one(
        "fs.storage",
        "Filesystem Storage",
        compute="_compute_fs_storage_id",
        help="The storage where the file is stored.",
        store=True,
        ondelete="restrict",
    )

    @api.depends("name")
    def _compute_internal_url(self) -> None:
        for rec in self:
            filename, extension = os.path.splitext(rec.name)
            # determine if the file is an image
            pfx = "/web/content"
            if rec.mimetype and rec.mimetype.startswith("image/"):
                pfx = "/web/image"

            if not extension:
                extension = mimetypes.guess_extension(rec.mimetype)
            rec.internal_url = f"{pfx}/{rec.id}/{filename}{extension}"

    @api.depends("fs_filename")
    def _compute_fs_url(self) -> None:
        for rec in self:
            new_url = None
            actual_url = rec.fs_url or None
            if rec.fs_filename:
                new_url = self.env["fs.storage"]._get_url_for_attachment(rec)
            # ensure we compare value of same type and not None with False
            new_url = new_url or None
            if new_url != actual_url:
                rec.fs_url = new_url

    @api.depends("fs_filename")
    def _compute_fs_url_path(self) -> None:
        for rec in self:
            rec.fs_url_path = None
            if rec.fs_filename:
                rec.fs_url_path = self.env["fs.storage"]._get_url_for_attachment(
                    rec, exclude_base_url=True
                )

    @api.depends("store_fname", "fs_filename")
    def _compute_fs_storage_id(self):
        for rec in self:
            if rec.store_fname:
                code = rec.store_fname.partition("://")[0]
                fs_storage = self.env["fs.storage"].sudo().get_by_code(code)
                if fs_storage != rec.fs_storage_id:
                    rec.fs_storage_id = fs_storage
            elif rec.fs_storage_id:
                rec.fs_storage_id = None

    @staticmethod
    def _is_storage_disabled(storage=None, log=True):
        msg = "Storages are disabled (see environment configuration)."
        if storage:
            msg = f"Storage '{storage}' is disabled (see environment configuration)."
        is_disabled = is_true(os.environ.get("DISABLE_ATTACHMENT_STORAGE"))
        if is_disabled and log:
            _logger.warning(msg)
        return is_disabled

    def _get_storage_force_db_config(self):
        return self.env["fs.storage"].get_force_db_for_default_attachment_rules(
            self._storage()
        )

    def _store_in_db_instead_of_object_storage_domain(self):
        """Return a domain for attachments that must be forced to DB

        Read the docstring of ``_store_in_db_instead_of_object_storage`` for
        more details.

        Used in ``force_storage_to_db_for_special_fields`` to find records
        to move from the object storage to the database.

        The domain must be inline with the conditions in
        ``_store_in_db_instead_of_object_storage``.
        """
        domain = []
        storage_config = self._get_storage_force_db_config()
        for mimetype_key, limit in storage_config.items():
            part = [("mimetype", "=like", f"{mimetype_key}%")]
            if limit:
                part = Domain.AND([part, [("file_size", "<=", limit)]])
            # OR simplifies to [(1, '=', 1)] if a domain being OR'ed is empty
            domain = Domain.OR([domain, part]) if domain else part
        return domain

    def _store_in_db_instead_of_object_storage(self, data, mimetype):
        """Return whether an attachment must be stored in db

        When we are using an Object Storage. This is sometimes required
        because the object storage is slower than the database/filesystem.

        Small images (128, 256) are used in Odoo in list / kanban views. We
        want them to be fast to read.
        They are generally < 50KB (default configuration) so they don't take
        that much space in database, but they'll be read much faster than from
        the object storage.

        The assets (application/javascript, text/css) are stored in database
        as well whatever their size is:

        * a database doesn't have thousands of them
        * of course better for performance
        * better portability of a database: when replicating a production
          instance for dev, the assets are included

        The configuration can be modified on the fs.storage record, in the
        field ``force_db_for_default_attachment_rules``, as a dictionary, for
        instance::

            {"image/": 51200, "application/javascript": 0, "text/css": 0}

        Where the key is the beginning of the mimetype to configure and the
        value is the limit in size below which attachments are kept in DB.
        0 means no limit.

        These limits are applied only if the storage is the default one for
        attachments (see ``_storage``).

        The conditions are also applied into the domain of the method
        ``_store_in_db_instead_of_object_storage_domain`` used to move records
        from a filesystem storage to the database.

        """
        if self._is_storage_disabled():
            return True
        storage_config = self._get_storage_force_db_config()
        for mimetype_key, limit in storage_config.items():
            if mimetype.startswith(mimetype_key):
                if not limit:
                    return True
                return data.size <= limit
        return False

    def _get_datas_related_values(self, data: BinaryValue, mimetype):
        # The store_fname into the filesystem storage is provided by
        # _file_fname. Here we only have to apply the rules forcing the
        # storage into the database.
        values = super()._get_datas_related_values(data, mimetype)
        if (
            data
            and self._storage() in self._get_storage_codes()
            and self._store_in_db_instead_of_object_storage(data, mimetype)
        ):
            values.update(
                {
                    "store_fname": False,
                    "db_datas": data,
                }
            )
        return values

    ###########################################################
    # Odoo methods that we override to use the object storage #
    ###########################################################
    @api.model
    def _storage(self):
        # An explicit storage can be given into the context
        storage = self.env.context.get("storage_location")
        if not storage:
            # We check if a filesystem storage is configured for attachments
            storage = self.env["fs.storage"].get_default_storage_code_for_attachments()
        if not storage:
            # If not, we use the default storage configured into odoo
            storage = super()._storage()
        return storage

    @api.model
    def _file_fname(self, sha: str) -> str:
        storage = self._storage()
        if storage in self._get_storage_codes() and not self._is_storage_disabled(
            storage, log=False
        ):
            # Uses the full object storage path; standard Odoo uses a
            # relative path.
            return f"{storage}://{self._get_fs_path(storage, sha)}"
        return super()._file_fname(sha)

    @api.autovacuum
    def _gc_file_store(self):
        # The odoo filestore can still contain files (attachments created
        # before the use of a filesystem storage, files uploaded through
        # _upload_file, ...). The base implementation only runs the GC if the
        # default storage is the odoo filestore.
        if self._storage() in self._get_storage_codes():
            self = self.with_context(storage_location="file")  # noqa: PLW0642
        return super()._gc_file_store()

    @api.model_create_multi
    def create(self, vals_list):
        """
        Storage may depend on resource field, but the method calling _storage
        (_get_datas_related_values) does not take all vals, just the mimetype.
        The only way to give res_field and res_model to _storage method
        is to pass them into the context, and perform 1 create call per record
        to create.
        """
        vals_list_no_model = []
        attachments = self.env["ir.attachment"]
        for vals in vals_list:
            if vals.get("res_model"):
                attachment = super(
                    IrAttachment,
                    self.with_context(
                        attachment_res_model=vals.get("res_model"),
                        attachment_res_field=vals.get("res_field"),
                    ),
                ).create(vals)
                attachments += attachment
            else:
                vals_list_no_model.append(vals)
        atts = super().create(vals_list_no_model)
        attachments |= atts
        if self.env.context.get("ir_attachment_from_stream") is not (
            CREATE_FROM_STREAM_FLAG
        ):
            # When created from a stream (see _upload_file), the file is
            # written after the creation of the attachment.
            attachments._enforce_meaningful_storage_filename()
        return attachments

    def _upload_file(self, file: io.IOBase, create_vals):
        attachment = super(
            IrAttachment,
            self.with_context(
                attachment_res_model=create_vals.get("res_model"),
                attachment_res_field=create_vals.get("res_field"),
            ),
        )._upload_file(file, create_vals)
        attachment = attachment.with_env(self.env)
        if self._is_file_from_a_storage(attachment.store_fname):
            if attachment._store_in_db_instead_of_object_storage(
                attachment.raw, attachment.mimetype
            ):
                # the mimetype and the size are only known once the file is
                # uploaded.
                attachment.write(
                    {"raw": attachment.raw, "mimetype": attachment.mimetype}
                )
            else:
                attachment._enforce_meaningful_storage_filename()
        return attachment

    def write(self, vals):
        if not self:
            return super().write(vals)
        if "raw" in vals and not ("name" in vals or "mimetype" in vals):
            if vals["raw"]:
                raw = self._fields["raw"].convert_to_cache(vals["raw"], self)
                vals = dict(vals, raw=raw)
            mimetype = self._compute_mimetype(vals)
            if mimetype and mimetype != "application/octet-stream":
                vals["mimetype"] = mimetype
            else:
                # When we write on an attachment, if the mimetype is not provided, it
                # will be computed from the name. The problem is that if you assign a
                # value to the field ``raw``, the name is not provided
                # nor the mimetype, so the mimetype will be set to ``application/octet-
                # stream``.
                # We want to avoid this, so we take the mimetype of the first attachment
                # and we set it on all the attachments if they all have the same
                # mimetype.
                # If they don't have the same mimetype, we raise an error.
                # OPW-3277070
                mimetypes = self.mapped("mimetype")
                if len(set(mimetypes)) == 1:
                    vals["mimetype"] = mimetypes[0]
                else:
                    raise UserError(
                        self.env._(
                            "You can't write on multiple attachments with different "
                            "mimetypes at the same time."
                        )
                    )
        for rec in self:
            # As when creating a new attachment, we must pass the res_field
            # and res_model into the context hence sadly we must perform 1 call
            # for each attachment.
            # vals is copied since it's modified in place by ir.attachment
            # (see _check_contents)
            super(
                IrAttachment,
                rec.with_context(
                    attachment_res_model=vals.get("res_model") or rec.res_model,
                    attachment_res_field=vals.get("res_field") or rec.res_field,
                ),
            ).write(dict(vals))

        if "name" in vals:
            self._enforce_meaningful_storage_filename()

        return True

    def _file_read(self) -> BinaryValue:
        if self._is_file_from_a_storage(self.store_fname):
            # lazy value: the content is only read from the storage when
            # accessed and can be streamed through its 'open' method.
            return FsBinaryFile(self)
        return super()._file_read()

    @api.model
    def _file_write(self, fname: str, bin_value: io.IOBase) -> None:
        if not self._is_file_from_a_storage(fname):
            return super()._file_write(fname, bin_value)
        fs, _storage, path = self._fs_parse_store_fname(fname)
        # Add the file to the list of files to garbage collect before writing
        # it, in case the transaction aborts. The GC only removes files no
        # more referenced by an attachment.
        self._fs_mark_for_gc(fname)
        dirname = os.path.dirname(path)
        if dirname and not fs.exists(dirname):
            fs.makedirs(dirname, exist_ok=True)
        kwargs = self._storage_write_option(fs)
        bin_value.seek(0)
        with fs.open(path, "wb", **kwargs) as f:
            shutil.copyfileobj(bin_value, f)

    @api.model
    def _file_delete(self, fname: str) -> None:
        if self._is_file_from_a_storage(fname):
            # The file is physically removed by the garbage collector if it's
            # no more referenced once the transaction is committed
            self._fs_mark_for_gc(fname)
        else:
            return super()._file_delete(fname)

    def _inverse_raw(self):
        res = super()._inverse_raw()
        self._enforce_meaningful_storage_filename()
        return res

    def _to_http_stream(self):
        self.ensure_one()
        if self._is_file_from_a_storage(self.store_fname):
            return FsStream.from_fs_attachment(self)
        return super()._to_http_stream()

    ##############################################
    # Internal methods to use the object storage #
    ##############################################
    def _storage_write_option(self, fs):
        return {}

    @api.model
    def _get_fs_path(self, storage_code: str, checksum: str) -> str:
        """Compute the path to store the file in the filesystem storage"""
        key = self.env.context.get("force_storage_key") or checksum
        if self.env["fs.storage"]._must_optimize_directory_path(storage_code):
            # Generate a unique directory path based on the file's hash
            key = os.path.join(key[:2], key[2:4], key)
        return key

    def _build_fs_filename(self):
        """Build the filename to store in the filesystem storage

        The filename is computed from the name, the extension and a version
        number. The version number is incremented each time we build a new
        filename. To know if a filename has already been build, we check if
        the fs_filename field is set. If it is set, we increment the version
        number. The version number is taken from the computed filename.

        The format of the filename is:
        <slugified name>-<id>-<version>.<extension>
        """
        self.ensure_one()
        filename, extension = os.path.splitext(self.name)
        if not extension:
            extension = mimetypes.guess_extension(self.mimetype)
        version = 0
        if self.fs_filename:
            parsed = self._parse_fs_filename(self.fs_filename)
            if parsed:
                version = parsed[2] + 1
        return "{}{}".format(
            slugify(
                f"{filename}-{self.id}-{version}",
                regex_pattern=REGEX_SLUGIFY,
            ),
            extension,
        )

    def _enforce_meaningful_storage_filename(self) -> None:
        """Enforce meaningful filename for files stored in the filesystem storage

        The filename of the file in the filesystem storage is computed from
        the mimetype and the name of the attachment. This method is called
        when an attachment is created to ensure that the filename of the file
        in the filesystem keeps the same meaning as the name of the attachment.

        Keeping the same meaning and mimetype is important to also ease to provide
        a meaningful and SEO friendly URL to the file in the filesystem storage.
        """
        renamed_attachments = {}
        for attachment in self:
            if not self._is_file_from_a_storage(attachment.store_fname):
                continue
            fs, storage, filename = attachment._get_fs_parts()

            if self.env["fs.storage"]._must_use_filename_obfuscation(storage):
                attachment.fs_filename = filename
                continue
            new_filename = attachment._build_fs_filename()
            # we must keep the same full path as the original filename
            new_filename_with_path = os.path.join(
                os.path.dirname(filename), new_filename
            )

            if filename in renamed_attachments:
                if renamed_attachments[filename] == new_filename_with_path:
                    # we already renamed this file, no need to rename it again
                    continue
                else:
                    fs.copy(renamed_attachments[filename], new_filename_with_path)
            else:
                fs.rename(filename, new_filename_with_path)
            renamed_attachments[filename] = new_filename_with_path

            attachment.fs_filename = new_filename
            # we need to update the store_fname with the new filename by
            # calling the write method of the field since the write method
            # of ir_attachment prevent normal write on store_fname
            attachment._force_write_store_fname(f"{storage}://{new_filename_with_path}")
            self._fs_mark_for_gc(attachment.store_fname)

    def _force_write_store_fname(self, store_fname):
        """Force the write of the store_fname field

        The write method of ir.attachment prevents the write of the
        store_fname field.
        """
        self._force_write_file_values({"store_fname": store_fname})

    def _force_write_file_values(self, vals):
        """Write the fields computed from the file content.

        The write method of ir.attachment ignores the fields 'checksum',
        'file_size' and 'store_fname'. This method bypasses this limitation by
        calling the write method of the parent class of ir.attachment (as done
        into ir.attachment._inverse_raw).
        """
        return super(BaseIrAttachment, self.sudo()).write(vals)

    def _fs_refresh_file_values(self):
        """Recompute the values depending on the file content (checksum,
        file_size and index_content) from the file into the filesystem storage.

        This method is called when the content of the file has been modified
        without using the 'raw' field (see the method 'open').
        """
        for rec in self:
            if not rec._is_file_from_a_storage(rec.store_fname):
                continue
            fs, _storage, path = rec._get_fs_parts()
            sha = hashlib.sha1()
            size = 0
            with fs.open(path, "rb") as f:
                while chunk := f.read(io.DEFAULT_BUFFER_SIZE):
                    sha.update(chunk)
                    size += len(chunk)
            checksum = sha.hexdigest()
            index_content = rec._index(FsBinaryFile(rec), rec.mimetype, checksum)
            rec._force_write_file_values(
                {
                    "checksum": checksum,
                    "file_size": size,
                    "index_content": index_content or False,
                }
            )

    @api.model
    def _get_fs_storage_for_code(
        self,
        code: str,
    ) -> fsspec.AbstractFileSystem | None:
        """Return the filesystem for the given storage code"""
        fs = self.env["fs.storage"].get_fs_by_code(code)
        if not fs:
            raise SystemError(f"No Filesystem storage for code {code}")
        return fs

    @api.model
    def _fs_parse_store_fname(
        self, fname: str
    ) -> tuple[fsspec.AbstractFileSystem, str, str]:
        """Return the filesystem, the storage code and the path for the given fname

        :param fname: the fname to parse
        :param base: if True, return the base filesystem
        """
        partition = fname.partition("://")
        storage_code = partition[0]
        fs = self._get_fs_storage_for_code(storage_code)
        fname = partition[2]
        return fs, storage_code, fname

    @api.model
    def _parse_fs_filename(self, filename: str) -> tuple[str, int, int, str] | None:
        """Parse the filename and return the name, id, version and extension
        <name-without-extension>-<id>-<version>.<extension>
        """
        if not filename:
            return None
        filename = os.path.basename(filename)
        match = FS_FILENAME_RE_PARSER.match(filename)
        if not match:
            return None
        name, res_id, version, extension = match.groups()
        return name, int(res_id), int(version), extension

    @api.model
    def _is_file_from_a_storage(self, fname):
        if not fname:
            return False
        for storage_code in self._get_storage_codes():
            if self._is_storage_disabled(storage_code):
                continue
            uri = f"{storage_code}://"
            if fname.startswith(uri):
                return True
        return False

    @api.model
    def _fs_mark_for_gc(self, fname):
        """Mark the file for deletion

        The file will be deleted by the garbage collector if it's no more
        referenced by any attachment. We use a garbage collector to enforce
        the transaction mechanism between Odoo and the filesystem storage.
        Files are added to the garbage collector when:
        - each time a file is created in the filesystem storage
        - an attachment is deleted

        Whatever the result of the current transaction, the information of files
        marked for deletion is stored in the database.

        When the garbage collector is called, it will check if the file is still
        referenced by an attachment. If not, the file is physically deleted from
        the filesystem storage.

        If the creation of the attachment fails, since the file is marked for
        deletion when it's written into the filesystem storage, it will be
        deleted by the garbage collector.

        If the content of the attachment is updated, we always create a new file.
        This new file is marked for deletion and the old one too. If the transaction
        succeeds, the old file is deleted by the garbage collector since it's no
        more referenced by any attachment. If the transaction fails, the old file
        is not deleted since it's still referenced by the attachment but the new
        file is deleted since it's marked for deletion and not referenced.
        """
        self.env["fs.file.gc"]._mark_for_gc(fname)

    def _get_fs_parts(
        self,
    ) -> tuple[fsspec.AbstractFileSystem, str, str] | tuple[None, None, None]:
        """Return the filesystem, the storage code and the path for the
        current attachment
        """
        if not self.store_fname:
            return None, None, None
        return self._fs_parse_store_fname(self.store_fname)

    def open(
        self,
        mode="rb",
        block_size=None,
        cache_options=None,
        compression=None,
        new_version=True,
        **kwargs,
    ) -> io.IOBase:
        """
        Return a file-like object from the filesystem storage where the attachment
        content is stored.

        In read mode, this method works for all attachments, even if the content
        is stored in the database or into the odoo filestore or a filesystem storage.
        If you only need to read the content, you can also use the standard
        ``attachment.raw.open()``: the value of the ``raw`` field is a lazy
        :class:`~odoo.tools.binary.BinaryValue` that streams the content from
        the storage.

        In write mode, if the content is not stored into a filesystem storage
        (database or odoo filestore), the content is written into a buffer in
        memory and assigned to the ``raw`` field when the file is closed.

        The resultant instance must function correctly in a context ``with``
        block.

        (parameters are ignored if the content is not stored into a
        filesystem storage).

        Parameters
        ----------
        path: str
            Target file
        mode: str like 'rb', 'w'
            See builtin ``open()``
        block_size: int
            Some indication of buffering - this is a value in bytes
        cache_options : dict, optional
            Extra arguments to pass through to the cache.
        compression: string or None
            If given, open file using compression codec. Can either be a compression
            name (a key in ``fsspec.compression.compr``) or "infer" to guess the
            compression from the filename suffix.
        new_version: bool
            If True, and mode is 'w', create a new version of the file.
            If False, and mode is 'w', overwrite the current version of the file.
            This flag is True by default to avoid data loss and ensure transaction
            mechanism between Odoo and the filesystem storage.
        encoding, errors, newline: passed on to TextIOWrapper for text mode

        Returns
        -------
        A file-like object

        TODO if open with 'w' in mode, we could use a buffered IO detecting that
        the content is modified and invalidating the attachment cache...
        """
        self.ensure_one()
        return AttachmentFileLikeAdapter(
            self,
            mode=mode,
            block_size=block_size,
            cache_options=cache_options,
            compression=compression,
            new_version=new_version,
            **kwargs,
        )

    @contextmanager
    def _do_in_new_env(self, new_cr=False):
        """Context manager that yields a new environment

        Using a new Odoo Environment thus a new PG transaction.
        """
        if new_cr:
            registry = Registry(self.env.cr.dbname)
            with closing(registry.cursor()) as cr:
                try:
                    yield self.env(cr=cr)
                except Exception:
                    cr.rollback()
                    raise
                else:
                    # disable pylint error because this is a valid commit,
                    # we are in a new env
                    cr.commit()  # pylint: disable=invalid-commit
        else:
            # make a copy
            yield self.env()

    def _get_storage_codes(self):
        """Get the list of filesystem storage active in the system"""
        return self.env["fs.storage"].sudo().get_storage_codes()

    def _get_x_sendfile_path(self):
        """Get the path to use for X-Accel-Redirect"""
        self.ensure_one()
        url_path = self.fs_url_path
        storage_code = self.fs_storage_code
        if not url_path:
            raise RuntimeError(
                f"The attachment {self.id} is not stored in a filesystem storage."
            )
        path = Path("/") / storage_code / url_path.lstrip("/")
        return str(path)

    def _fs_use_x_sendfile(self):
        """Return whether to use X-Sendfile to serve the internal URL"""
        self.ensure_one()
        return (
            self.fs_url_path and self.fs_storage_id.use_x_sendfile_to_serve_internal_url
        )

    ################################
    # useful methods for migration #
    ################################

    def _move_attachment_to_store(self):
        self.ensure_one()
        _logger.info("inspecting attachment %s (%d)", self.name, self.id)
        fname = self.store_fname
        if fname:
            storage = fname.partition("://")[0]
            if self._is_storage_disabled(storage):
                fname = False
        if fname:
            if (
                not self._is_file_from_a_storage(fname)
                and not Path(self._full_path(fname)).exists()
            ):
                _logger.warning("file %s does not exist, skipping migration", fname)
                return
            # migrating from filesystem filestore
            # or from the old 'store_fname' without the bucket name
            _logger.info("moving %s on the object storage", fname)
            self.write(
                {
                    "raw": self.raw,
                    # this is required otherwise the
                    # mimetype gets overriden with
                    # 'application/octet-stream'
                    # on assets
                    "mimetype": self.mimetype,
                }
            )
            _logger.info("moved %s on the object storage", fname)
            return self._full_path(fname)
        elif self.db_datas:
            _logger.info("moving on the object storage from database")
            self.write({"raw": self.raw, "mimetype": self.mimetype})

    @api.model
    def force_storage(self):
        if not self.env.is_admin():
            raise AccessError(
                self.env._("Only administrators can execute this action.")
            )
        location = self.env.context.get("storage_location") or self._storage()
        if location not in self._get_storage_codes():
            return super().force_storage()
        self._force_storage_to_object_storage()

    @api.model
    def force_storage_to_db_for_special_fields(
        self, new_cr=False, storage: str | None = None
    ):
        """Migrate special attachments from Object Storage back to database

        The access to a file stored on the objects storage is slower
        than a local disk or database access. For attachments like
        image_small that are accessed in batch for kanban views, this
        is too slow. We store this type of attachment in the database.

        This method can be used when migrating a filestore where all the files,
        including the special files (assets, image_small, ...) have been pushed
        to the Object Storage and we want to write them back in the database.

        It is not called anywhere, but can be called by RPC or scripts.
        """
        if not storage:
            storage = self._storage()
        if self._is_storage_disabled(storage):
            _logger.warning(
                "Storage '%s' is disabled, skipping migration of attachments to DB",
                storage,
            )
            return
        if storage not in self._get_storage_codes():
            _logger.warning(
                "Storage '%s' is not configured, "
                "skipping migration of attachments to DB",
                storage,
            )
            return

        domain = Domain.AND(
            (
                Domain.AND(
                    [
                        Domain("store_fname", "=like", f"{storage}://%"),
                        # for res_field, see comment in
                        # _force_storage_to_object_storage
                        Domain.OR(
                            [
                                Domain("res_field", "=", False),
                                Domain("res_field", "!=", False),
                            ]
                        ),
                    ]
                ),
                Domain(self._store_in_db_instead_of_object_storage_domain()),
            )
        )

        with self._do_in_new_env(new_cr=new_cr) as new_env:
            model_env = new_env["ir.attachment"].with_context(prefetch_fields=False)
            attachment_ids = model_env.search(domain).ids
            if not attachment_ids:
                return
            total = len(attachment_ids)
            start_time = time.time()
            _logger.info(
                "Moving %d attachments from %s to DB for fast access", total, storage
            )
            for current, attachment_id in enumerate(attachment_ids, start=1):
                # if we browse attachments outside of the loop, the first
                # access to 'raw' will compute all the 'raw' fields at
                # once, which means reading hundreds or thousands of files at
                # once, exhausting memory
                attachment = model_env.browse(attachment_id)
                # this write will read the raw from the Object Storage and
                # write them back in the DB (the logic for location to write is
                # in the 'raw' inverse computed field)
                # we need to write the mimetype too, otherwise it will be
                # overwritten with 'application/octet-stream' on assets. On each
                # write, the mimetype is recomputed if not given. If we don't
                # pass it nor the name, the mimetype will be set to the default
                # value 'application/octet-stream' on assets.
                attachment.write(
                    {"raw": attachment.raw, "mimetype": attachment.mimetype}
                )
                if current % 100 == 0 or total - current == 0:
                    _logger.info(
                        "attachment %s/%s after %.2fs",
                        current,
                        total,
                        time.time() - start_time,
                    )

    @api.model
    def _force_storage_to_object_storage(self, new_cr=False):
        _logger.info("migrating files to the object storage")
        storage = self.env.context.get("storage_location") or self._storage()
        if self._is_storage_disabled(storage):
            return
        # The weird "res_field = False OR res_field != False" domain
        # is required! It's because of an override of _search in ir.attachment
        # which adds ('res_field', '=', False) when the domain does not
        # contain 'res_field'.
        # https://github.com/odoo/odoo/blob/9032617120138848c63b3cfa5d1913c5e5ad76db/
        # odoo/addons/base/ir/ir_attachment.py#L344-L347
        domain = [
            "!",
            ("store_fname", "=like", f"{storage}://%"),
            "|",
            ("res_field", "=", False),
            ("res_field", "!=", False),
        ]
        # We do a copy of the environment so we can workaround the cache issue
        # below. We do not create a new cursor by default because it causes
        # serialization issues due to concurrent updates on attachments during
        # the installation
        with self._do_in_new_env(new_cr=new_cr) as new_env:
            model_env = new_env["ir.attachment"]
            ids = model_env.search(domain).ids
            files_to_clean = []
            for attachment_id in ids:
                try:
                    with new_env.cr.savepoint():
                        # check that no other transaction has
                        # locked the row, don't send a file to storage
                        # in that case
                        self.env.cr.execute(
                            "SELECT id "
                            "FROM ir_attachment "
                            "WHERE id = %s "
                            "FOR UPDATE NOWAIT",
                            (attachment_id,),
                            log_exceptions=False,
                        )

                        # This is a trick to avoid having the 'raw'
                        # function fields computed for every attachment on
                        # each iteration of the loop. The former issue
                        # being that it reads the content of the file of
                        # ALL the attachments on each loop.
                        new_env.invalidate_all()
                        attachment = model_env.browse(attachment_id)
                        path = attachment._move_attachment_to_store()
                        if path:
                            files_to_clean.append(path)
                except psycopg2.OperationalError:
                    _logger.error(
                        "Could not migrate attachment %s to S3", attachment_id
                    )

            # delete the files from the filesystem once we know the changes
            # have been committed in ir.attachment
            if files_to_clean:
                new_env.cr.commit()
                clean_fs(files_to_clean)


class AttachmentFileLikeAdapter:
    """
    This class is a wrapper class around the ir.attachment model. It is used to
    open the ir.attachment as a file and to read/write data to it.

    When the content of the file is stored into the odoo filestore or in a
    filesystem storage, this object allows you to read/write the content from
    the file in a direct way without having to read/write the whole file into
    memory. When the content of the file is stored into database, this content
    is read/written from/into a buffer in memory.

    Parameters
    ----------
    attachment : ir.attachment
        The attachment to open as a file.
    mode: str like 'rb', 'w'
            See builtin ``open()``
    block_size: int
        Some indication of buffering - this is a value in bytes
    cache_options : dict, optional
        Extra arguments to pass through to the cache.
    compression: string or None
        If given, open file using compression codec. Can either be a compression
        name (a key in ``fsspec.compression.compr``) or "infer" to guess the
        compression from the filename suffix.
    new_version: bool
        If True, and mode is 'w', create a new version of the file.
        If False, and mode is 'w', overwrite the current version of the file.
        This flag is True by default to avoid data loss and ensure transaction
        mechanism between Odoo and the filesystem storage.
    encoding, errors, newline: passed on to TextIOWrapper for text mode

    You can use this class to adapt an attachment object as a file in 2 ways:
     * as a context manager wrapping the attachment object as a file
     * or as a nomral utility class

    Examples

    >>> with AttachmentFileLikeAdapter(attachment, mode="rb") as f:
    ...     f.read()
    b'Hello World'
    # at the end of the context manager, the file is closed
    >>> f = AttachmentFileLikeAdapter(attachment, mode="rb")
    >>> f.read()
    b'Hello World'
    # you have to close the file manually
    >>> f.close()

    """

    def __init__(
        self,
        attachment: IrAttachment,
        mode: str = "rb",
        block_size: int | None = None,
        cache_options: dict | None = None,
        compression: str | None = None,
        new_version: bool = False,
        **kwargs,
    ):
        self._attachment = attachment
        self._mode = mode
        self._block_size = block_size
        self._cache_options = cache_options
        self._compression = compression
        self._new_version = new_version
        self._kwargs = kwargs

        # state attributes
        self._file: io.IOBase | None = None
        self._buffer: io.BytesIO | None = None
        self._filesystem: fsspec.AbstractFileSystem | None = None
        self._new_store_fname: str | None = None

    @property
    def attachment(self) -> IrAttachment:
        """The attachment object the file is related to"""
        return self._attachment

    @property
    def mode(self) -> str:
        """The mode used to open the file"""
        return self._mode

    @property
    def block_size(self) -> int | None:
        """The block size used to open the file"""
        return self._block_size

    @property
    def cache_options(self) -> dict | None:
        """The cache options used to open the file"""
        return self._cache_options

    @property
    def compression(self) -> str | None:
        """The compression used to open the file"""
        return self._compression

    @property
    def new_version(self) -> bool:
        """Is the file open for a new version"""
        return self._new_version

    @property
    def kwargs(self) -> dict:
        """The kwargs passed when opening the file on the"""
        return self._kwargs

    @property
    def _is_open_for_modify(self) -> bool:
        """Is the file open for modification
        A file is open for modification if it is open for writing or appending
        """
        return any(flag in self.mode for flag in "wax+")

    @property
    def _is_open_for_read(self) -> bool:
        """Is the file open for reading"""
        return "r" in self.mode

    @property
    def _is_stored_in_fs_storage(self) -> bool:
        """Is the file currently stored into a filesystem storage"""
        return self.attachment._is_file_from_a_storage(self.attachment.store_fname)

    @property
    def _target_storage_is_fs_storage(self) -> bool:
        """Is the storage to use for new content a filesystem storage"""
        attachment = self.attachment
        storage = attachment.with_context(
            attachment_res_model=attachment.res_model,
            attachment_res_field=attachment.res_field,
        )._storage()
        return storage in attachment._get_storage_codes() and not (
            attachment._is_storage_disabled(storage, log=False)
        )

    def __enter__(self) -> io.IOBase:
        """Called when entering the context manager

        Create the file object and return it.
        """
        # we call the attachment instance to get the file object
        self._file_open()
        return self._file

    def _fs_open_kwargs(self) -> dict:
        return dict(
            mode=self.mode,
            block_size=self.block_size,
            cache_options=self.cache_options,
            compression=self.compression,
            **self.kwargs,
        )

    def _file_open(self) -> io.IOBase:
        """Open the attachment content as a file-like object

        This method will initialize the following attributes:

        * _file: the file-like object.
        * _filesystem: filesystem object if the file is opened on a
          filesystem storage.
        * _buffer: the in memory buffer if the content is not written into
          a filesystem storage.
        * _new_store_fname: the new store_fname if the file is
          opened for a new version.
        """
        attachment = self.attachment
        if not self._is_open_for_modify:
            if self._is_stored_in_fs_storage:
                fs, _storage, path = attachment._get_fs_parts()
                self._filesystem = fs
                self._file = fs.open(path, **self._fs_open_kwargs())
            else:
                # database or odoo filestore: rely on the lazy value
                # provided by odoo
                self._file = self._wrap_text_mode(attachment.raw.open())
        elif self._is_stored_in_fs_storage and not self.new_version:
            # modify the file in place
            fs, _storage, path = attachment._get_fs_parts()
            self._filesystem = fs
            self._file = fs.open(path, **self._fs_open_kwargs())
        elif self.new_version and self._target_storage_is_fs_storage:
            self._file = self._open_new_version()
        else:
            # The content is stored into the database or into the odoo
            # filestore where files are shared between attachments with
            # the same content and therefore can't be modified in place.
            # We write the content into a buffer that will be assigned to
            # the raw field when the file is closed.
            self._buffer = io.BytesIO()
            if "a" in self.mode or "+" in self.mode:
                with attachment.raw.open() as f:
                    shutil.copyfileobj(f, self._buffer)
                if "a" not in self.mode:
                    self._buffer.seek(0)
            self._file = self._wrap_text_mode(self._buffer)
        return self._file

    def _wrap_text_mode(self, file: io.IOBase) -> io.IOBase:
        if "b" in self.mode:
            return file
        return io.TextIOWrapper(
            file,
            encoding=self.kwargs.get("encoding"),
            errors=self.kwargs.get("errors"),
            newline=self.kwargs.get("newline"),
        )

    def _open_new_version(self) -> io.IOBase:
        """Create a new file into the filesystem storage and open it

        We must create a new file with a new name. If we are in an append
        mode, we must copy the content of the old file (or create the new one
        by copy of the old one). The name of the new file is computed as
        for a new content (see ir.attachment._file_fname) from a random
        checksum to avoid collision.
        """
        attachment = self.attachment
        checksum = attachment._compute_checksum(self._gen_random_content())
        new_store_fname = attachment.with_context(
            attachment_res_model=attachment.res_model,
            attachment_res_field=attachment.res_field,
        )._file_fname(checksum)
        filesystem, storage, new_filepath = attachment._fs_parse_store_fname(
            new_store_fname
        )
        # the new file must be garbage collected if the transaction aborts
        attachment._fs_mark_for_gc(new_store_fname)
        dirname = os.path.dirname(new_filepath)
        if dirname and not filesystem.exists(dirname):
            filesystem.makedirs(dirname, exist_ok=True)
        if "a" in self.mode or "+" in self.mode:
            old_store_fname = attachment.store_fname or ""
            if old_store_fname.partition("://")[0] == storage:
                _fs, _storage, old_filepath = attachment._get_fs_parts()
                filesystem.cp_file(old_filepath, new_filepath)
            else:
                with (
                    attachment.raw.open() as src,
                    filesystem.open(new_filepath, "wb") as dst,
                ):
                    shutil.copyfileobj(src, dst)
        self._filesystem = filesystem
        self._new_store_fname = new_store_fname
        return filesystem.open(new_filepath, **self._fs_open_kwargs())

    def _gen_random_content(self, size=256):
        """Generate a random content of size bytes"""
        return os.urandom(size)

    def _file_close(self):
        """Close the file-like object opened by _file_open"""
        if not self._file:
            return
        if self._buffer is not None:
            if self._file is not self._buffer:
                # text mode: flush the content into the buffer without
                # closing it
                self._file.flush()
                self._file.detach()
            content = self._buffer.getvalue()
            self._buffer.close()
            self._buffer = None
            self._file = None
            self.attachment.write({"raw": content})
            self._ensure_cache_consistency()
            return
        if not self._file.closed:
            self._file.flush()
            self._file.close()
        if self._is_open_for_modify:
            if self._new_store_fname:
                self.attachment._force_write_store_fname(self._new_store_fname)
            self.attachment._fs_refresh_file_values()
            if self._new_store_fname:
                self.attachment._enforce_meaningful_storage_filename()
            self._ensure_cache_consistency()

    def _ensure_cache_consistency(self):
        """Ensure the cache consistency once the file is closed"""
        if self._is_open_for_modify:
            self.attachment.invalidate_recordset(fnames=["raw"])
        if (
            self.attachment.res_model
            and self.attachment.res_id
            and self.attachment.res_field
            and self.attachment.res_model in self.attachment.env
        ):
            self.attachment.env[self.attachment.res_model].browse(
                self.attachment.res_id
            ).invalidate_recordset(fnames=[self.attachment.res_field])

    def __exit__(self, *args):
        """Called when exiting the context manager.

        Close the file if it is not already closed.
        """
        self._file_close()

    def __getattr__(self, attr):
        """
        Forward all other attributes to the underlying file object.

        This method is required to make the object behave like a file object
        when the AttachmentFileLikeAdapter is used outside a context manager.

        .. code-block:: python

           f = AttachmentFileLikeAdapter(attachment)
           f.read()

        """
        if not self._file:
            self.__enter__()
        return getattr(self._file, attr)


class FsBinaryFile(BinaryValue):
    """Lazily loaded file stored into a filesystem storage.

    This is the counterpart of the odoo's ``LocalBinaryFile`` for the files
    stored into a filesystem storage. The content is only read from the
    storage when accessed. The ``open`` method allows to stream the content
    without loading it into memory.
    """

    __slots__ = (
        "__checksum",
        "__content",
        "__fs",
        "__path",
        "__size",
        "__storage",
        "filename",
    )

    def __init__(self, record: IrAttachment):
        fs, storage, path = record._get_fs_parts()
        self.__fs: fsspec.AbstractFileSystem = fs
        self.__storage: str = storage
        self.__path: str = path
        self.__checksum: str = record.checksum
        self.__size: int = record.file_size
        self.__content: bytes | None = None
        self.filename = record.name

    def open(self) -> io.IOBase:
        if self.__content is not None:
            return super().open()
        return self.__fs.open(self.__path, "rb")

    @property
    def content(self) -> bytes:
        if self.__content is None:
            try:
                with self.open() as f:
                    self.__content = f.read()
            except OSError:
                _logger.info(
                    "Error reading %s on storage %s",
                    self.__path,
                    self.__storage,
                    exc_info=True,
                )
                self.__content = b""
        return self.__content

    @property
    def size(self) -> int:
        if self.__size or self.__content is not None:
            return self.__size or len(self.__content)
        return len(self.content)

    @property
    def checksum(self) -> str:
        return self.__checksum or super().checksum

    def __bool__(self):
        return bool(self.size)

    def __repr__(self):
        return f"FsBinaryFile({self.__storage}://{self.__path})"
