# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    # small and medium image are here to replace
    # native image field on form and kanban
    variant_image_small_url = fields.Char(
        related="variant_image_ids.image_id.image_small_url",
        store=True,
        string="Variant Image Small Url",
    )
    variant_image_medium_url = fields.Char(
        related="variant_image_ids.image_id.image_medium_url",
        store=True,
        string="Variant Image Medium Url",
    )
    variant_image_ids = fields.Many2many(
        "product.image.relation",
        compute="_compute_variant_image_ids",
        store=True,
        string="Variant Images",
    )

    @api.depends(
        "product_tmpl_id.image_ids.attribute_value_ids",
        "product_template_attribute_value_ids",
    )
    def _compute_variant_image_ids(self):
        for variant in self:
            res = self.env["product.image.relation"].browse([])
            for image in variant.image_ids:
                if not (
                    image.attribute_value_ids
                    - variant.mapped(
                        "product_template_attribute_value_ids."
                        "product_attribute_value_id"
                    )
                ):
                    res |= image
            variant.variant_image_ids = res
