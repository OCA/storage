# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class FsProductCategoryMedia(models.Model):
    _name = "fs.product.category.media"
    _inherit = "fs.media.relation.mixin"
    _description = "Product Category Media"

    product_categ_id = fields.Many2one(
        comodel_name="product.category",
        string="Product Category",
        ondelete="cascade",
        index=True,
    )
