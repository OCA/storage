# Copyright 2017-2013 Camptocamp SA
# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import io
import logging
import mimetypes
import os
import re
import time
from contextlib import closing, contextmanager

import fsspec  # pylint: disable=missing-manifest-dependency
import psycopg2
from slugify import slugify  # pylint: disable=missing-manifest-dependency

import odoo
from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.osv.expression import AND, OR, normalize_domain

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
            except IOError:
                # Harmless and needed for race conditions
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
            if not extension:
                extension = mimetypes.guess_extension(rec.mimetype)
            rec.internal_url = f"/web/content/{rec.id}/{filename}{extension}"

    @api.depends("fs_filename")
    def _compute_fs_url(self) -> None:
        for rec in self:
            rec.fs_url = None
            if rec.fs_filename:
                rec.fs_url = self.env["fs.storage"]._get_url_for_attachment(rec)

    @api.depends("fs_filename")
    def _compute_fs_url_path(self) -> None:
        for rec in self:
            rec.fs_url_path = None
            if rec.fs_filename:
                rec.fs_url_path = self.env["fs.storage"]._get_url_for_attachment(
                    rec, exclude_base_url=True
                )

    @api.depends("fs_filename")
    def _compute_fs_storage_id(self):
        for rec in self:
            if rec.store_fname:
                code = rec.store_fname.partition("://")[0]
                fs_storage = self.env["fs.storage"].get_by_code(code)
                if fs_storage != rec.fs_storage_id:
                    rec.fs_storage_id = fs_storage
            elif rec.fs_storage_id:
                rec.fs_storage_id = None

    @staticmethod
    def _is_storage_disabled(storage=None, log=True):
        msg = _("Storages are disabled (see environment configuration).")
        if storage:
            msg = _("Storage '%s' is disabled (see environment configuration).") % (
                storage,
            )
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
            part = [("mimetype", "=like", "{}%".format(mimetype_key))]
            if limit:
                part = AND([part, [("file_size", "<=", limit)]])
            domain = OR([domain, part])
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
                bin_data = data
                return len(bin_data) <= limit
        return False

    def _get_datas_related_values(self, data, mimetype):
        storage = self.env.context.get("storage_location") or self._storage()
        if data and storage in self._get_storage_codes():
            if self._store_in_db_instead_of_object_storage(data, mimetype):
                # compute the fields that depend on datas
                bin_data = data
                values = {
                    "file_size": len(bin_data),
                    "checksum": self._compute_checksum(bin_data),
                    "index_content": self._index(bin_data, mimetype),
                    "store_fname": False,
                    "db_datas": data,
                }
                return values
        return super()._get_datas_related_values(data, mimetype)

    ###########################################################
    # Odoo methods that we override to use the object storage #
    ###########################################################
    @api.model
    def _storage(self):
        # We check if a filesystem storage is configured for attachments
        storage = self.env["fs.storage"].get_default_storage_code_for_attachments()
        if not storage:
            # If not, we use the default storage configured into odoo
            storage = super()._storage()
        return storage

    @api.model_create_multi
    def create(self, vals_list):
        attachments = super().create(vals_list)
        attachments._enforce_meaningful_storage_filename()
        return attachments

    def write(self, vals):
        if not self:
            return self
        if ("datas" in vals or "raw" in vals) and not (
            "name" in vals or "mimetype" in vals
        ):
            # When we write on an attachment, if the mimetype is not provided, it
            # will be computed from the name. The problem is that if you assign a
            # value to the field ``datas`` or ``raw``, the name is not provided
            # nor the mimetype, so the mimetype will be set to ``application/octet-
            # stream``.
            # We want to avoid this, so we take the mimetype of the first attachment
            # and we set it on all the attachments if they all have the same mimetype.
            # If they don't have the same mimetype, we raise an error.
            # OPW-3277070
            mimetypes = self.mapped("mimetype")
            if len(set(mimetypes)) == 1:
                vals["mimetype"] = mimetypes[0]
            else:
                raise UserError(
                    _(
                        "You can't write on multiple attachments with different "
                        "mimetypes at the same time."
                    )
                )
        return super().write(vals)

    @api.model
    def _file_read(self, fname):
        if self._is_file_from_a_storage(fname):
            return self._storage_file_read(fname)
        else:
            return super()._file_read(fname)

    @api.model
    def _file_write(self, bin_data, checksum):
        location = self.env.context.get("storage_location") or self._storage()
        if location in self._get_storage_codes():
            filename = self._storage_file_write(bin_data)
        else:
            filename = super()._file_write(bin_data, checksum)
        return filename

    @api.model
    def _file_delete(self, fname) -> None:  # pylint: disable=missing-return
        if self._is_file_from_a_storage(fname):
            cr = self.env.cr
            # using SQL to include files hidden through unlink or due to record
            # rules
            cr.execute(
                "SELECT COUNT(*) FROM ir_attachment WHERE store_fname = %s", (fname,)
            )
            count = cr.fetchone()[0]
            if not count:
                self._storage_file_delete(fname)
        else:
            super()._file_delete(fname)

    def _set_attachment_data(self, asbytes) -> None:  # pylint: disable=missing-return
        super()._set_attachment_data(asbytes)
        self._enforce_meaningful_storage_filename()

    ##############################################
    # Internal methods to use the object storage #
    ##############################################
    @api.model
    def _storage_file_read(self, fname: str) -> bytes | None:
        """Read the file from the filesystem storage"""
        fs, _storage, fname = self._fs_parse_store_fname(fname, root=True)
        with fs.open(fname, "rb") as fs:
            return fs.read()

    @api.model
    def _storage_file_write(self, bin_data: bytes) -> str:
        """Write the file to the filesystem storage"""
        storage = self.env.context.get("storage_location") or self._storage()
        fs = self._get_fs_storage_for_code(storage)
        path = self._get_fs_path(storage, bin_data)
        dirname = os.path.dirname(path)
        if not fs.exists(dirname):
            fs.makedirs(dirname)
        fname = f"{storage}://{path}"
        with fs.open(path, "wb") as fs:
            fs.write(bin_data)
        self._fs_mark_for_gc(fname)
        return fname

    @api.model
    def _storage_file_delete(self, fname):
        """Delete the file from the filesystem storage

        It's safe to use the fname (the store_fname) to delete the file because
        even if it's the full path to the file, the gc will only delete the file
        if they belong to the configured storage directory path.
        """
        self._fs_mark_for_gc(fname)

    @api.model
    def _get_fs_path(self, storage_code: str, bin_data: bytes) -> str:
        """Compute the path to store the file in the filesystem storage"""
        key = self.env.context.get("force_storage_key")
        if not key:
            key = self._compute_checksum(bin_data)
        if self.env["fs.storage"]._must_optimize_directory_path(storage_code):
            # Generate a unique directory path based on the file's hash
            key = os.path.join(key[:2], key[2:4], key)
        # Generate a unique directory path based on the file's hash
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
            version = self._parse_fs_filename(self.fs_filename)[2] + 1
        return "{}{}".format(
            slugify(
                "{}-{}-{}".format(filename, self.id, version),
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
        for attachment in self:
            if not self._is_file_from_a_storage(attachment.store_fname):
                continue
            fs, storage, filename = self._fs_parse_store_fname(attachment.store_fname)
            if self.env["fs.storage"]._must_use_filename_obfuscation(storage):
                attachment.fs_filename = fs.info(filename)["name"]
                continue
            if self._is_fs_filename_meaningful(filename):
                continue
            new_filename = attachment._build_fs_filename()
            # we must keep the same full path as the original filename
            new_filename = os.path.join(os.path.dirname(filename), new_filename)
            fs.rename(filename, new_filename)
            new_filename = fs.info(new_filename)["name"]
            attachment.fs_filename = new_filename
            # we need to update the store_fname with the new filename by
            # calling the write method of the field since the write method
            # of ir_attachment prevent normal write on store_fname
            attachment._fields["store_fname"].write(
                attachment, f"{storage}://{new_filename}"
            )
            self._fs_mark_for_gc(attachment.store_fname)

    @api.model
    def _get_fs_storage_for_code(
        self, code: str, root: bool = False
    ) -> fsspec.AbstractFileSystem | None:
        """Return the filesystem for the given storage code"""
        fs = self.env["fs.storage"].get_fs_by_code(code, root=root)
        if not fs:
            raise SystemError(f"No Filesystem storage for code {code}")
        return fs

    @api.model
    def _fs_parse_store_fname(
        self, fname: str, root: bool = False
    ) -> tuple[fsspec.AbstractFileSystem, str, str]:
        """Return the filesystem, the storage code and the path for the given fname

        :param fname: the fname to parse
        :param base: if True, return the base filesystem
        """
        partition = fname.partition("://")
        storage_code = partition[0]
        fs = self._get_fs_storage_for_code(storage_code, root=root)
        fname = partition[2]
        return fs, storage_code, fname

    @api.model
    def _is_fs_filename_meaningful(self, filename: str) -> bool:
        """Return True if the filename is meaningful
        A filename is meaningful if it's formatted as
        """
        parsed = self._parse_fs_filename(filename)
        if not parsed:
            return False
        name, res_id, version, extension = parsed
        return bool(name and res_id and version is not None and extension)

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
            uri = "{}://".format(storage_code)
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

    def open(
        self, mode="rb", block_size=None, cache_options=None, compression=None, **kwargs
    ) -> io.IOBase:
        """
        Return a file-like object from the filesystem storage where the attachment
        content is stored.

        This method works for all attachments, even if the content is stored in the
        database or into the odoo filestore. (parameters are ignored in the case
        of the database storage).

        The resultant instance must function correctly in a context ``with``
        block.

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
        encoding, errors, newline: passed on to TextIOWrapper for text mode

        Returns
        -------
        A file-like object

        Caution: modifications to the file-like object are not transactional.
        If you modify the file-like object and the current transaction is rolled
        back, the changes will be saved to the file and not rolled back.
        Moreover mofication to the content will not be reflected into the cache
        and could lead to data mismatch when the data will be flush

        TODO if open with 'w' in mode, we could use a buffered IO detecting that
        the content is modified and invalidating the attachment cache...
        """
        self.ensure_one()
        if self._is_file_from_a_storage(self.store_fname):
            fs, _storage, fname = self._fs_parse_store_fname(
                self.store_fname, root=True
            )
            return fs.open(
                fname,
                mode=mode,
                block_size=block_size,
                cache_options=cache_options,
                compression=compression,
                **kwargs,
            )
        if self.store_fname:
            return fsspec.filesystem("file").open(
                self._full_path(self.store_fname),
                mode=mode,
                block_size=block_size,
                cache_options=cache_options,
                compression=compression,
                **kwargs,
            )
        if "w" in mode:
            raise SystemError("Write mode is not supported for data read from database")
        return io.BytesIO(self.db_datas)

    @contextmanager
    def _do_in_new_env(self, new_cr=False):
        """Context manager that yields a new environment

        Using a new Odoo Environment thus a new PG transaction.
        """
        if new_cr:
            registry = odoo.modules.registry.Registry.new(self.env.cr.dbname)
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

    ################################
    # useful methods for migration #
    ################################

    def _move_attachment_to_store(self):
        self.ensure_one()
        _logger.info("inspecting attachment %s (%d)", self.name, self.id)
        fname = self.store_fname
        storage = fname.partition("://")[0]
        if self._is_storage_disabled(storage):
            fname = False
        if fname:
            # migrating from filesystem filestore
            # or from the old 'store_fname' without the bucket name
            _logger.info("moving %s on the object storage", fname)
            self.write(
                {
                    "datas": self.datas,
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
            self.write({"datas": self.datas})

    @api.model
    def force_storage(self):
        if not self.env["res.users"].browse(self.env.uid)._is_admin():
            raise AccessError(_("Only administrators can execute this action."))
        location = self.env.context.get("storage_location") or self._storage()
        if location not in self._get_storage_codes():
            return super().force_storage()
        self._force_storage_to_object_storage()

    @api.model
    def force_storage_to_db_for_special_fields(self, new_cr=False):
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
        storage = self._storage()
        if self._is_storage_disabled(storage):
            return
        if storage not in self._get_storage_codes():
            return

        domain = AND(
            (
                normalize_domain(
                    [
                        ("store_fname", "=like", "{}://%".format(storage)),
                        # for res_field, see comment in
                        # _force_storage_to_object_storage
                        "|",
                        ("res_field", "=", False),
                        ("res_field", "!=", False),
                    ]
                ),
                normalize_domain(self._store_in_db_instead_of_object_storage_domain()),
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
                "Moving %d attachments from %s to" " DB for fast access", total, storage
            )
            current = 0
            for attachment_id in attachment_ids:
                current += 1
                # if we browse attachments outside of the loop, the first
                # access to 'datas' will compute all the 'datas' fields at
                # once, which means reading hundreds or thousands of files at
                # once, exhausting memory
                attachment = model_env.browse(attachment_id)
                # this write will read the datas from the Object Storage and
                # write them back in the DB (the logic for location to write is
                # in the 'datas' inverse computed field)
                # we need to write the mimetype too, otherwise it will be
                # overwritten with 'application/octet-stream' on assets. On each
                # write, the mimetype is recomputed if not given. If we don't
                # pass it nor the name, the mimetype will be set to the default
                # value 'application/octet-stream' on assets.
                attachment.write({"datas": attachment.datas})
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
            ("store_fname", "=like", "{}://%".format(storage)),
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

                        # This is a trick to avoid having the 'datas'
                        # function fields computed for every attachment on
                        # each iteration of the loop. The former issue
                        # being that it reads the content of the file of
                        # ALL the attachments on each loop.
                        new_env.clear()
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
