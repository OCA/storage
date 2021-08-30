# Copyright 2020 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ProductBrandImageRelation(models.Model):
    _name = "product.brand.image.relation"
    _inherit = "image.relation.abstract"
    _description = "Product Brand Image Relation"

    brand_id = fields.Many2one(
        "product.brand",
        required=True,
        ondelete="cascade",
    )
    tag_id = fields.Many2one(
        "image.tag",
        string="tag",
        domain=[("apply_on", "=", "brand")],
    )
