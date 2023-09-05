# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from odoo.addons.fs_file import fields as fs_fields


class FsMediaRelationMixin(models.AbstractModel):

    _name = "fs.media.relation.mixin"
    _description = "Media Relation"
    _order = "sequence, name"
    _rec_name = "name"

    sequence = fields.Integer()
    link_existing = fields.Boolean(
        string="Link existing media",
        default=False,
    )
    media_id = fields.Many2one(
        comodel_name="fs.media",
        string="Linked media",
    )
    specific_file = fs_fields.FSFile("Specific Media")
    specific_media_type_id = fields.Many2one(
        "fs.media.type",
    )
    file = fs_fields.FSFile("Media", compute="_compute_media", store=False)
    media_type_id = fields.Many2one(
        "fs.media.type", compute="_compute_media", store=False
    )
    name = fields.Char(compute="_compute_name", store=True, index=True)
    mimetype = fields.Char(compute="_compute_mimetype", store=True)

    @api.depends("file")
    def _compute_name(self):
        for record in self:
            record.name = record.file.name if record.file else None

    @api.depends("file")
    def _compute_mimetypes(self):
        for record in self:
            record.mimetype = record.file.mimetype if record.file else None

    @api.depends("media_id", "specific_file", "link_existing")
    def _compute_media(self):
        for record in self:
            if record.link_existing:
                record.file = record.media_id.file
                record.media_type_id = record.media_id.media_type_id
            else:
                record.file = record.specific_file
                record.media_type_id = record.specific_media_type_id

    @api.model
    def _cleanup_vals(self, vals):
        if (
            "link_existing" in vals
            and vals["link_existing"]
            and "specific_file" in vals
        ):
            vals["specific_file"] = False
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._cleanup_vals(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._cleanup_vals(vals)
        return super().write(vals)
