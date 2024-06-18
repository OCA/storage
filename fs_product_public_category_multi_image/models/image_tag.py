# Copyright 2024 ForgeFlow (http://www.forgeflow.com).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import api, fields, models


class ImageTag(models.Model):
    _inherit = "image.tag"

    @api.model
    def _get_default_apply_on(self):
        active_model = self.env.context.get("active_model")
        return (
            "public.category"
            if active_model == "public.category.image.relation"
            else super()._get_default_apply_on()
        )

    apply_on = fields.Selection(
        selection_add=[("public.category", "Public Category")],
        ondelete={"product": "cascade", "category": "cascade"},
    )
