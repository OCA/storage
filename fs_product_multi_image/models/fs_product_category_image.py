# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class FsProductCategoryImage(models.Model):
    _name = "fs.product.category.image"
    _inherit = "fs.image.relation.mixin"
    _description = "Product Category Image"

    product_categ_id = fields.Many2one(
        comodel_name="product.category",
        string="Product Category",
        ondelete="cascade",
        index=True,
    )

    tag_id = fields.Many2one(
        "image.tag",
        string="Tag",
        domain=[("apply_on", "=", "category")],
        index=True,
    )
