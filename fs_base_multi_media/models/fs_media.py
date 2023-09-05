# Copyright 2017 Akretion (http://www.akretion.com).
# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import api, fields, models

from odoo.addons.fs_file.fields import FSFile


class FsMedia(models.Model):
    _name = "fs.media"
    _description = "Media"

    file = FSFile(required=True)
    name = fields.Char(compute="_compute_name", store=True, index=True)
    mimetype = fields.Char(compute="_compute_mimetype", store=True)
    media_type_id = fields.Many2one("fs.media.type", "Media Type")

    @api.depends("file")
    def _compute_name(self):
        for record in self:
            record.name = record.file.name if record.file else None

    @api.depends("file")
    def _compute_mimetype(self):
        for record in self:
            record.mimetype = record.file.mimetype if record.file else None
