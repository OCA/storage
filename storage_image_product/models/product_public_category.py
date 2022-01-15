# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ProductPublicCategory(models.Model):
    _inherit = "product.public.category"

    image_ids = fields.One2many(
        "public.category.image.relation", inverse_name="public_category_id"
    )
