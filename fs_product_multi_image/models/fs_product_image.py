# Copyright 2023 ACSONE SA/NV
# Copyright 2018 Akretion (http://www.akretion.com).
# @author Raphaël Reverdy <https://github.com/hparfr>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FsProductImage(models.Model):
    _name = "fs.product.image"
    _inherit = "fs.image.relation.mixin"
    _description = "Product Image"

    product_tmpl_id = fields.Many2one(
        comodel_name="product.template",
        string="Product Template",
        ondelete="cascade",
        index=True,
    )
    attribute_value_ids = fields.Many2many(
        "product.attribute.value",
        string="Attributes",
        domain="[('id', 'in', available_attribute_value_ids)]",
    )
    # This field will list all attribute value used by the template
    # in order to filter the attribute value available for the current image
    available_attribute_value_ids = fields.Many2many(
        "product.attribute.value",
        string="Available Attributes",
        compute="_compute_available_attribute",
    )
    tag_id = fields.Many2one(
        "image.tag",
        string="Tag",
        domain=[("apply_on", "=", "product")],
        index=True,
    )

    @api.depends("product_tmpl_id.attribute_line_ids.value_ids")
    def _compute_available_attribute(self):
        for rec in self:
            rec.available_attribute_value_ids = rec.product_tmpl_id.mapped(
                "attribute_line_ids.value_ids"
            )

    def _match_variant(self, variant):
        variant_attribute_values = variant.mapped(
            "product_template_attribute_value_ids.product_attribute_value_id"
        )
        return not bool(self.attribute_value_ids - variant_attribute_values)
