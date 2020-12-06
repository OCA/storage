# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductBrandImageRelation(models.Model):
    _name = "product.brand.image.relation"
    _inherit = "image.relation.abstract"
    _description = "Product Brand Image Relation"

    brand_id = fields.Many2one("product.brand")
