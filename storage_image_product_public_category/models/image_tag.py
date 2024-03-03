# Copyright 2023 ForgeFlow (http://www.forgeflow.com).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import api, fields, models


class ImageTag(models.Model):
    _inherit = "image.tag"
    _description = "Image Tag"

    @api.model
    def _get_default_apply_on(self):
        active_model = self.env.context.get("active_model")
        return (
            "product"
            if active_model == "product.image.relation"
            else "category"
            if active_model == "category.image.relation"
            else "public.category"
            if active_model == "public.category.image.relation"
            else False
        )

    apply_on = fields.Selection(selection_add=[("public.category", "Public Category")])
