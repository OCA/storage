# Copyright 2024 ForgeFlow (http://www.forgeflow.com).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class FsProductPublicCategoryImage(models.Model):
    _name = "fs.product.public.category.image"
    _inherit = "fs.image.relation.mixin"
    _description = "Product Public Category Image"

    public_category_id = fields.Many2one(
        "product.public.category",
        required=True,
        ondelete="cascade",
        index=True,
    )
    tag_id = fields.Many2one(
        "image.tag",
        string="Tag",
        domain=[("apply_on", "=", "public.category")],
        index=True,
    )
