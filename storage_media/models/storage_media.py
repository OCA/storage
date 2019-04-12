# -*- coding: utf-8 -*-
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

    file_id = fields.Many2one(
        "storage.file", "File", required=True, ondelete="cascade"
    )
    media_type_id = fields.Many2one("storage.media.type", "Media Type")

    @api.onchange("name")
    def onchange_name(self):
        for record in self:
            if record.name:
                filename, extension = os.path.splitext(record.name)
                record.name = "{}{}".format(slugify(filename), extension)

    @api.model
    def create(self, vals):
        vals["file_type"] = "media"
        if "backend_id" not in vals:
            vals["backend_id"] = self._get_backend_id()
        return super(StorageMedia, self).create(vals)

    def _get_backend_id(self):
        """Choose the correct backend.

        By default : it's the one configured as ir.config_parameter
        Overload this method if you need something more powerfull
        """
        return int(
            self.env["ir.config_parameter"].get_param(
                "storage.media.backend_id"
            )
        )
