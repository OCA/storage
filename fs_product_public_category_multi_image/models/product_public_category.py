# Copyright 2024 ForgeFlow (http://www.forgeflow.com).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models

from odoo.addons.fs_image.fields import FSImage


class ProductPublicCategory(models.Model):
    _inherit = "product.public.category"

    image_ids = fields.One2many(
        string="Images",
        comodel_name="fs.product.public.category.image",
        inverse_name="public_category_id",
    )
    image = FSImage(related="image_ids.image", readonly=True, store=False)
    image_medium = FSImage(related="image_ids.image_medium", readonly=True, store=False)
