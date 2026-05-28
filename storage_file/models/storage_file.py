# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
import hashlib
import logging
import mimetypes
import os
import re

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import SQL, human_size

_logger = logging.getLogger(__name__)

try:
    from slugify import slugify
except ImportError:  # pragma: no cover
    _logger.debug("Cannot `import slugify`.")


REGEX_SLUGIFY = r"[^-a-z0-9_]+"


class StorageFile(models.Model):
    _name = "storage.file"
    _description = "Storage File"

    name = fields.Char(required=True, index=True)
    backend_id = fields.Many2one(
        "storage.backend",
        "Storage",
        index=True,
        required=True,
        default=lambda self: self._get_default_backend_id(),
    )
    url = fields.Char(compute="_compute_url", help="HTTP accessible path to the file")
    url_path = fields.Char(
        compute="_compute_url_path", help="Accessible path, no base URL"
    )
    internal_url = fields.Char(
        compute="_compute_internal_url",
        help="HTTP URL to load the file directly from storage.",
    )
    slug = fields.Char(
        compute="_compute_slug", help="Slug-ified name with ID for URL", store=True
    )
    relative_path = fields.Char(help="Relative location for backend", copy=False)
    file_size = fields.Integer()
    human_file_size = fields.Char(compute="_compute_human_file_size", store=True)
    checksum = fields.Char("Checksum/SHA1", size=40, index=True)
    filename = fields.Char(
        "Filename without extension", compute="_compute_extract_filename", store=True
    )
    extension = fields.Char(compute="_compute_extract_filename", store=True)
    mimetype = fields.Char("Mime Type", compute="_compute_extract_filename", store=True)
    data = fields.Binary(
        help="Data",
        inverse="_inverse_data",
        compute="_compute_data",
        store=False,
        copy=True,
    )
    to_delete = fields.Boolean()
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company", "Company", default=lambda self: self.env.user.company_id.id
    )
    file_type = fields.Selection([])
    is_public = fields.Boolean(
        compute="_compute_is_public",
        compute_sudo=True,
        search="_search_is_public",
        # Not stored to avoid massive recomputes when the backend flag changes.
        help="Reflects the `is_public` flag of the related backend.",
    )

    @api.depends("backend_id.is_public")
    def _compute_is_public(self):
        for rec in self:
            rec.is_public = rec.backend_id.is_public

    @api.model
    def _get_default_backend_id(self):
        return self.env["storage.backend"]._get_backend_id_from_param(
            self.env, "storage.file.backend_id"
        )

    def _search_is_public(self, operator, value):
        # Look up matching backends with sudo so that users with limited ACL
        # on `storage.backend` can still filter their accessible files by
        # public flag.
        backends = (
            self.env["storage.backend"].sudo().search([("is_public", operator, value)])
        )
        return [("backend_id", "in", backends.ids)]

    _sql_constraints = [
        (
            "path_uniq",
            "unique(relative_path, backend_id)",
            "The private path must be uniq per backend",
        )
    ]

    def write(self, vals):
        if "data" in vals:
            for record in self:
                if record.data:
                    raise UserError(
                        self.env._(
                            "File can not be updated, remove it and create a new one"
                        )
                    )
        if "backend_id" in vals and not self.env.context.get(
            "storage_file_swap_backend"
        ):
            new_backend = self.env["storage.backend"].browse(vals["backend_id"])
            to_swap = self.filtered(
                lambda r: r.backend_id and r.backend_id != new_backend
            )
            if to_swap:
                to_swap._swap_backend(new_backend)
                remaining = self - to_swap
                if remaining:
                    return super(StorageFile, remaining).write(vals)
                return True
        return super().write(vals)

    @api.depends("file_size")
    def _compute_human_file_size(self):
        for record in self:
            record.human_file_size = human_size(record.file_size)

    @api.depends("filename", "extension")
    def _compute_slug(self):
        for record in self:
            record.slug = record._slugify_name_with_id()

    def _slugify_name_with_id(self):
        return "{}{}".format(
            slugify(f"{self.filename}-{self.id}", regex_pattern=REGEX_SLUGIFY),
            self.extension,
        )

    def _build_relative_path(self, checksum):
        self.ensure_one()
        strategy = self.sudo().backend_id.filename_strategy
        if not strategy:
            raise UserError(
                self.env._(
                    "The filename strategy is empty for the backend %s.\n"
                    "Please configure it"
                ).format(self.backend_id.name)
            )
        if strategy == "hash":
            return checksum[:2] + "/" + checksum
        elif strategy == "name_with_id":
            return self.slug

    def _prepare_meta_for_file(self):
        bin_data = base64.b64decode(self.data)
        checksum = hashlib.sha1(bin_data).hexdigest()
        relative_path = self._build_relative_path(checksum)
        return {
            "checksum": checksum,
            "file_size": len(bin_data),
            "relative_path": relative_path,
        }

    def _inverse_data(self):
        for record in self:
            record.write(record._prepare_meta_for_file())
            record.backend_id.sudo().add(
                record.relative_path,
                record.data,
                mimetype=record.mimetype,
                binary=False,
            )

    def _compute_data(self):
        for rec in self:
            if self._context.get("bin_size"):
                rec.data = rec.file_size
            elif rec.relative_path:
                rec.data = rec.backend_id.sudo().get(rec.relative_path, binary=False)
            else:
                rec.data = None

    @api.depends("relative_path", "backend_id")
    def _compute_url(self):
        for record in self:
            record.url = record._get_url()

    @api.depends("relative_path", "backend_id")
    def _compute_url_path(self):
        # Keep this separated from `url` to avoid multiple compute:
        # you'll need either one or the other.
        for record in self:
            record.url_path = record._get_url(exclude_base_url=True)

    def _get_url(self, exclude_base_url=False):
        """Retrieve file URL based on backend params.

        :param exclude_base_url: skip base_url
        """
        if not self.backend_id or not self.relative_path:
            return ""
        return self.backend_id._get_url_for_file(
            self, exclude_base_url=exclude_base_url
        )

    @api.depends("slug")
    def _compute_internal_url(self):
        for record in self:
            record.internal_url = record._get_internal_url()

    def _get_internal_url(self):
        """Retrieve file URL to load file directly from the storage.

        It is recommended to use this for Odoo backend internal usage
        to not generate traffic on external services.
        """
        return f"/storage.file/{self.slug}"

    @api.depends("name")
    def _compute_extract_filename(self):
        for rec in self:
            if rec.name:
                rec.filename, rec.extension = os.path.splitext(rec.name)
                mime, __ = mimetypes.guess_type(rec.name)
            else:
                rec.filename = rec.extension = mime = False
            rec.mimetype = mime

    def unlink(self):
        if self._context.get("cleanning_storage_file"):
            super().unlink()
        else:
            self.write({"to_delete": True, "active": False})
        return True

    @api.model
    def _clean_storage_file(self, batch_size=1000):
        # we must be sure that all the changes are into the DB since
        # we by pass the ORM
        self.flush_model(["to_delete"])
        self._cr.execute(
            SQL("""SELECT id
            FROM storage_file
            WHERE to_delete=True FOR UPDATE""")
        )
        ids = [x[0] for x in self._cr.fetchall()]
        recordset = self.browse(ids[:batch_size])
        for st_file in recordset:
            st_file.backend_id.sudo().delete(st_file.relative_path)
            st_file.with_context(cleanning_storage_file=True).unlink()
            # commit is required since the backend could be an external system
            # therefore, if the record is deleted on the external system
            # we must be sure that the record is also deleted into Odoo
            st_file._cr.commit()
        done = len(recordset)
        self.env["ir.cron"]._notify_progress(
            done=done, remaining=0 if done <= batch_size else len(ids) - done
        )

    def _swap_backend(self, new_backend):
        """Swap files to ``new_backend``.

        For each record:

        - read binary data from the current backend storage,
        - upload it to the new backend (re-computing relative_path using the
          new backend filename strategy),
        - update ``backend_id`` and ``relative_path`` on the record,
        - delete the old file from the previous backend.

        Files already on ``new_backend`` are skipped.

        :return: dict with ``moved`` (list of names) and ``failed`` (list of
            error descriptions).
        """
        if not new_backend:
            raise UserError(self.env._("A destination storage is required."))
        new_backend = new_backend.sudo()
        if not new_backend.filename_strategy:
            raise UserError(
                self.env._(
                    "The filename strategy is empty for the backend %s.\n"
                    "Please configure it.",
                    new_backend.name,
                )
            )
        moved = []
        failed = []
        for record in self.sudo():
            if not record.exists():
                failed.append(f"ID {record.id}: record no longer exists")
                continue
            if record.backend_id == new_backend:
                continue
            old_backend = record.backend_id
            old_relative_path = record.relative_path
            try:
                if not old_relative_path:
                    record.with_context(
                        storage_file_swap_backend=True
                    ).backend_id = new_backend
                    moved.append(f"{record.name} (ID {record.id})")
                    continue
                bin_data = old_backend.get(old_relative_path, binary=True)
                # Same logic as _build_relative_path but using the target
                # backend strategy (backend_id not yet reassigned).
                strategy = new_backend.filename_strategy
                if strategy == "hash":
                    new_relative_path = record.checksum[:2] + "/" + record.checksum
                else:
                    new_relative_path = record.slug
                new_backend.add(
                    new_relative_path,
                    bin_data,
                    mimetype=record.mimetype,
                    binary=True,
                )
                record.with_context(storage_file_swap_backend=True).write(
                    {
                        "backend_id": new_backend.id,
                        "relative_path": new_relative_path,
                    }
                )
                try:
                    old_backend.delete(old_relative_path)
                except Exception as exc:
                    _logger.warning(
                        "Swapped %s but failed to delete old file %s from %s: %s",
                        record.name,
                        old_relative_path,
                        old_backend.name,
                        exc,
                    )
                moved.append(f"{record.name} (ID {record.id})")
            except Exception as exc:
                failed.append(f"{record.name} (ID {record.id}): {exc}")
                _logger.exception(
                    "Failed to swap file %s (ID %d) to backend %s",
                    record.name,
                    record.id,
                    new_backend.name,
                )
        return {"moved": moved, "failed": failed}

    @api.model
    def get_from_slug_name_with_id(self, slug_name_with_id):
        """
        Return a browse record from a string generated by the method
        _slugify_name_with_id
        :param slug_name_with_id:
        :return: a BrowseRecord (could be empty...)
        """
        # id is the last group of digit after '-'
        _id = re.findall(r"-([0-9]+)", slug_name_with_id)[-1:]
        if _id:
            _id = int(_id[0])
        return self.browse(_id)
