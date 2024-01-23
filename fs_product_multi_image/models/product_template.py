# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from odoo.addons.fs_image.fields import FSImage


class ProductTemplate(models.Model):

    _inherit = "product.template"

    image_ids = fields.One2many(
        string="Images", comodel_name="fs.product.image", inverse_name="product_tmpl_id"
    )
    main_image_id = fields.Many2one(
        string="Main Image",
        comodel_name="fs.product.image",
        compute="_compute_main_image_id",
        # Store it to improve perfs
        store=True,
    )
    image = FSImage(related="main_image_id.image", readonly=True, store=False)
    image_medium = FSImage(
        related="main_image_id.image_medium", readonly=True, store=False
    )

    @api.depends("image_ids", "image_ids.sequence")
    def _compute_main_image_id(self):
        for record in self:
            image_ids = record.image_ids.sorted(
                key=lambda i: f"{i.sequence},{str(i.id)}"
            )
            record.main_image_id = image_ids and image_ids[0] or None
