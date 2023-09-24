# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from odoo.addons.fs_image import fields as fs_fields


class FsImage(models.Model):

    _name = "fs.image"
    _inherit = "fs.image.mixin"
    _description = "Image"
    _order = "name, id"
    _rec_name = "name"

    image = fs_fields.FSImage(required=True)  # makes field required
    name = fields.Char(compute="_compute_name", store=True, index=True)
    mimetype = fields.Char(compute="_compute_mimetype", store=True)

    @api.depends("image")
    def _compute_name(self):
        for record in self:
            record.name = record.image.name if record.image else None

    @api.depends("image")
    def _compute_mimetypes(self):
        for record in self:
            record.mimetype = record.image.mimetype if record.image else None
