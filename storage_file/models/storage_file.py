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
from odoo.tools import human_size
from odoo.tools.translate import _

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
        "storage.backend", "Storage", index=True, required=True
    )
    url = fields.Char(compute="_compute_url", help="HTTP accessible path to the file")
    internal_url = fields.Char(
        compute="_compute_internal_url",
        help="HTTP URL to load the file directly from storage.",
    )
    slug = fields.Char(
        compute="_compute_slug", help="Slug-ified name with ID for URL", store=True
    )
    relative_path = fields.Char(readonly=True, help="Relative location for backend")
    file_size = fields.Integer("File Size")
    human_file_size = fields.Char(
        "Human File Size", compute="_compute_human_file_size", store=True
    )
    checksum = fields.Char("Checksum/SHA1", size=40, index=True, readonly=True)
    filename = fields.Char(
        "Filename without extension", compute="_compute_extract_filename", store=True
    )
    extension = fields.Char(
        "Extension", compute="_compute_extract_filename", store=True
    )
    mimetype = fields.Char("Mime Type", compute="_compute_extract_filename", store=True)
    data = fields.Binary(
        help="Datas", inverse="_inverse_data", compute="_compute_data", store=False
    )
    to_delete = fields.Boolean()
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company", "Company", default=lambda self: self.env.user.company_id.id
    )
    file_type = fields.Selection([])

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
                        _("File can not be updated," "remove it and create a new one")
                    )
        return super(StorageFile, self).write(vals)

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
            slugify(
                "{}-{}".format(self.filename, self.id), regex_pattern=REGEX_SLUGIFY
            ),
            self.extension,
        )

    def _build_relative_path(self, checksum):
        self.ensure_one()
        strategy = self.sudo().backend_id.filename_strategy
        if not strategy:
            raise UserError(
                _(
                    "The filename strategy is empty for the backend %s.\n"
                    "Please configure it"
                )
                % self.backend_id.name
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

    def _get_url(self):
        """Retrieve file URL based on backend params."""
        return self.backend_id._get_url_for_file(self)

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
            super(StorageFile, self).unlink()
        else:
            self.write({"to_delete": True, "active": False})
        return True

    @api.model
    def _clean_storage_file(self):
        # we must be sure that all the changes are into the DB since
        # we by pass the ORM
        self.flush()
        self._cr.execute(
            """SELECT id
            FROM storage_file
            WHERE to_delete=True FOR UPDATE"""
        )
        ids = [x[0] for x in self._cr.fetchall()]
        for st_file in self.browse(ids):
            st_file.backend_id.sudo().delete(st_file.relative_path)
            st_file.with_context(cleanning_storage_file=True).unlink()
            # commit is required since the backend could be an external system
            # therefore, if the record is deleted on the external system
            # we must be sure that the record is also deleted into Odoo
            st_file._cr.commit()

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
