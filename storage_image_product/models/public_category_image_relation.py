# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class PublicCategoryImageRelation(models.Model):
    _name = "public.category.image.relation"
    _inherit = "image.relation.abstract"
    _description = "Public Category Image Relation"

    public_category_id = fields.Many2one(
        "product.public.category",
        required=True,
        ondelete="cascade",
    )
    tag_id = fields.Many2one(
        "image.tag",
        string="Tag",
        domain=[("apply_on", "=", "public.category")],
    )
