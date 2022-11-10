# Copyright 2018 Akretion (http://www.akretion.com).
# @author Raphaël Reverdy <https://github.com/hparfr>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import api, fields, models


class ImageTag(models.Model):
    _name = "image.tag"
    _inherit = ["server.env.techname.mixin"]
    _description = "Image Tag"

    @api.model
    def _get_default_apply_on(self):
        active_model = self.env.context.get("active_model")
        return (
            "product"
            if active_model == "product.image.relation"
            else "category"
            if active_model == "category.image.relation"
            else False
        )

    name = fields.Char(required=True)
    apply_on = fields.Selection(
        selection=[("product", "Product"), ("category", "Category")],
        default=lambda self: self._get_default_apply_on(),
    )
