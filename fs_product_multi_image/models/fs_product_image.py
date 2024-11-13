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
    image_url = fields.Char(compute="_compute_image_url")

    @api.depends("image")
    def _compute_image_url(self):
        for record in self:
            record.image_url = False
            if record.image:
                record.image_url = self._get_url()

    def _get_url(self):
        product_id = False
        if "params" in self.env.context:
            id = self.env.context["params"]["id"]
            product_id = self.env["product.product"].browse(id)
        name = product_id.barcode if product_id else self.product_tmpl_id.name
        return f"/web/image/fs.product.image/{self.id}/image?download=true&filename={name}.jpg"

    def download_image_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return f"{base_url}{self._get_url()}"

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
