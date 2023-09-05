# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from odoo.addons.fs_image.fields import FSImage


class ProductCategory(models.Model):

    _inherit = "product.category"

    image_ids = fields.One2many(
        string="Images",
        comodel_name="fs.product.category.image",
        inverse_name="product_categ_id",
    )
    image = FSImage(related="image_ids.image", readonly=True, store=False)
    image_medium = FSImage(related="image_ids.image_medium", readonly=True, store=False)
