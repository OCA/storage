# Copyright 2018 Akretion (http://www.akretion.com).
# @author Raphaël Reverdy <https://github.com/hparfr>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class CategoryImageRelation(models.Model):
    _name = "category.image.relation"
    _inherit = "image.relation.abstract"
    _description = "Category Image Relation"

    category_id = fields.Many2one(
        "product.category",
        required=True,
        ondelete="cascade",
    )
    tag_id = fields.Many2one(
        "image.tag",
        string="Tag",
        domain=[("apply_on", "=", "category")],
    )
