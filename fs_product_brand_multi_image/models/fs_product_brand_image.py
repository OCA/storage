# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class FsProductBrandImage(models.Model):
    _name = "fs.product.brand.image"
    _inherit = "fs.image.relation.mixin"
    _description = "Product Brand Image"

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
