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

    # deprecated fields, kept for backward compatibility
    # uses specific_image_128 instead of specific_image_medium
    specific_image_medium = fs_fields.FSImage(
        "Specific Image medium",
        related="specific_image_128",
    )
    specific_image_1024 = fs_fields.FSImage(
        "Specific Image (1024)",
        related="specific_image",
        max_width=1024,
        max_height=1024,
        store=True,
    )
    specific_image_512 = fs_fields.FSImage(
        "Specific Image (512)",
        related="specific_image",
        max_width=512,
        max_height=512,
        store=True,
    )
    specific_image_256 = fs_fields.FSImage(
        "Specific Image (256)",
        related="specific_image",
        max_width=256,
        max_height=256,
        store=True,
    )
    specific_image_128 = fs_fields.FSImage(
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

    # deprecated fields, kept for backward compatibility
    # uses image_128 instead of image_medium
    image_medium = fs_fields.FSImage("Image medium", related="image_128", store=False)
    image_1024 = fs_fields.FSImage(
        "Image (1024)", compute="_compute_image_1024", store=False
    )
    image_512 = fs_fields.FSImage(
        "Image (512)", compute="_compute_image_512", store=False
    )
    image_256 = fs_fields.FSImage(
        "Image (256)", compute="_compute_image_256", store=False
    )
    image_128 = fs_fields.FSImage(
        "Image (128)", compute="_compute_image_128", store=False
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

    @api.depends("image_id", "specific_image_128", "link_existing")
    def _compute_image_128(self):
        for record in self:
            if record.link_existing:
                record.image_128 = record.image_id.image_128
            else:
                record.image_128 = record.specific_image_128

    @api.depends("image_id", "specific_image_256", "link_existing")
    def _compute_image_256(self):
        for record in self:
            if record.link_existing:
                record.image_256 = record.image_id.image_256
            else:
                record.image_256 = record.specific_image_256

    @api.depends("image_id", "specific_image_512", "link_existing")
    def _compute_image_512(self):
        for record in self:
            if record.link_existing:
                record.image_512 = record.image_id.image_512
            else:
                record.image_512 = record.specific_image_512

    @api.depends("image_id", "specific_image_1024", "link_existing")
    def _compute_image_1024(self):
        for record in self:
            if record.link_existing:
                record.image_1024 = record.image_id.image_1024
            else:
                record.image_1024 = record.specific_image_1024

    def _inverse_image(self):
        for record in self:
            if not record.link_existing:
                record.specific_image = record.image

    @api.model
    def _cleanup_vals(self, vals):
        link_existing = vals.get("link_existing")
        if link_existing:
            if "specific_image" in vals:
                vals.pop("specific_image")
            if "image" in vals:
                # image is set when using the kanban renderer so it
                # prevents the name field to be computed well
                vals.pop("image")
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._cleanup_vals(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._cleanup_vals(vals)
        return super().write(vals)
