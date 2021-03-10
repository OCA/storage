# Copyright 2020 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ProductBrand(models.Model):

    _inherit = "product.brand"

    image_small_url = fields.Char(
        related="image_ids.image_id.image_small_url", store=True
    )
    image_medium_url = fields.Char(
        related="image_ids.image_id.image_medium_url", store=True
    )
    image_ids = fields.One2many(
        comodel_name="product.brand.image.relation",
        inverse_name="brand_id",
        string="Images",
    )
