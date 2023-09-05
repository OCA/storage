# Copyright 2021 Akretion (https://www.akretion.com).
# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import api, fields, models


class ImageTag(models.Model):
    _inherit = "image.tag"

    @api.model
    def _get_default_apply_on(self):
        active_model = self.env.context.get("active_model")
        if active_model == "product.brand.image.relation":
            return "brand"
        else:
            return super()._get_default_apply_on()

    apply_on = fields.Selection(
        selection_add=[("brand", "Brand")],
        ondelete={"brand": "cascade"},
    )
