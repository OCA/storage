# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductCategory(models.Model):

    _inherit = "product.category"

    media_ids = fields.One2many(
        string="Medias",
        comodel_name="fs.product.category.media",
        inverse_name="product_categ_id",
    )
