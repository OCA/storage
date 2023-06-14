# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models


class ProductPublicCategory(models.Model):
    _inherit = "product.public.category"

    media_ids = fields.Many2many("storage.media")
