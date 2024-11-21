# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# Copyright 2021 Camptocamp (http://www.camptocamp.com).
# @author Iván Todorovich <ivan.todorovich@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


import logging
import os

from odoo import api, fields, models

from odoo.addons.storage_file.models.storage_file import REGEX_SLUGIFY

_logger = logging.getLogger(__name__)

try:
    from slugify import slugify
except ImportError:  # pragma: no cover
    _logger.debug("Cannot `import slugify`.")


class StorageImage(models.Model):
    _name = "storage.image"
    _description = "Storage Image"
    _inherit = "thumbnail.mixin"
    _inherits = {"storage.file": "file_id"}
    _default_file_type = "image"

    alt_name = fields.Char(string="Alt Image name")
    file_id = fields.Many2one("storage.file", "File", required=True, ondelete="cascade")

    @api.onchange("name")
    def onchange_name(self):
        for record in self:
            if record.name:
                filename, extension = os.path.splitext(record.name)
                record.name = (
                    f"{slugify(filename, regex_pattern=REGEX_SLUGIFY)}{extension}"
                )
                record.alt_name = filename
                for char in ["-", "_"]:
                    record.alt_name = record.alt_name.replace(char, " ")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["file_type"] = self._default_file_type
            if "backend_id" not in vals:
                vals["backend_id"] = self._get_default_backend_id()
        return super().create(vals_list)

    def _get_default_backend_id(self):
        return self.env["storage.backend"]._get_backend_id_from_param(
            self.env, "storage.image.backend_id"
        )

    def unlink(self):
        files = self.mapped("file_id")
        thumbnails = self.mapped("thumbnail_ids")
        return super().unlink() and thumbnails.unlink() and files.unlink()
