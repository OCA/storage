# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import os

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

try:
    from slugify import slugify
except ImportError:  # pragma: no cover
    _logger.debug("Cannot `import slugify`.")


class StorageMedia(models.Model):
    _name = "storage.media"
    _description = "Storage Media"
    _inherits = {"storage.file": "file_id"}
    _default_file_type = "media"

    file_id = fields.Many2one("storage.file", "File", required=True, ondelete="cascade")
    media_type_id = fields.Many2one("storage.media.type", "Media Type")

    @api.onchange("name")
    def onchange_name(self):
        for record in self:
            if record.name:
                filename, extension = os.path.splitext(record.name)
                record.name = "{}{}".format(slugify(filename), extension)

    @api.model
    def create(self, vals):
        vals["file_type"] = self._default_file_type
        if "backend_id" not in vals:
            vals["backend_id"] = self._get_default_backend_id()
        return super(StorageMedia, self).create(vals)

    def _get_default_backend_id(self):
        return self.env["storage.backend"]._get_backend_id_from_param(
            self.env, "storage.media.backend_id"
        )
