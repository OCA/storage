# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.fs_image import fields as fs_fields


class FsImageRelationMixin(models.AbstractModel):

    _name = "fs.image.relation.mixin"
    _description = "Image Relation"
    _order = "sequence, name"
    _rec_name = "name"

    sequence = fields.Integer()
    image_id = fields.Many2one(
        comodel_name="fs.image",
        string="Linked image",
    )
    specific_image = fs_fields.FSImage("Specific Image")
    # resized fields stored (as attachment) for performance
    specific_image_medium = fs_fields.FSImage(
        "Specific Image (128)",
        related="specific_image",
        max_width=128,
        max_height=128,
        store=True,
    )
    link_existing = fields.Boolean(default=False)

    image = fs_fields.FSImage(
        "Image (original)",
        compute="_compute_image",
        inverse="_inverse_image",
        store=False,
    )
    # resized fields stored (as attachment) for performance
    image_medium = fs_fields.FSImage(
        "Image (128)", compute="_compute_image_medium", store=False
    )

    name = fields.Char(compute="_compute_name", store=True, index=True)
    mimetype = fields.Char(compute="_compute_mimetype", store=True)

    @api.constrains("specific_image", "image_id")
    def _check_image(self):
        for record in self:
            if not record.image_id and not record.specific_image:
                raise ValidationError(_("You must set an image"))

    @api.depends("image")
    def _compute_name(self):
        for record in self:
            record.name = record.image.name if record.image else None

    @api.depends("image")
    def _compute_mimetypes(self):
        for record in self:
            record.mimetype = record.image.mimetype if record.image else None

    @api.depends("image_id", "specific_image", "link_existing")
    def _compute_image(self):
        for record in self:
            if record.link_existing:
                record.image = record.image_id.image
            else:
                record.image = record.specific_image

    @api.depends("image_id", "specific_image", "link_existing")
    def _compute_image_medium(self):
        for record in self:
            if record.link_existing:
                record.image_medium = record.image_id.image_medium
            else:
                record.image_medium = record.specific_image_medium

    def _inverse_image(self):
        for record in self:
            if not record.link_existing:
                record.specific_image = record.image

    @api.model
    def _cleanup_vals(self, vals):
        if (
            "link_existing" in vals
            and vals["link_existing"]
            and "specific_image" in vals
        ):
            vals["specific_image"] = False
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._cleanup_vals(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._cleanup_vals(vals)
        return super().write(vals)
