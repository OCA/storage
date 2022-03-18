from odoo import models


class ProductTemplateAttributeLine(models.Model):

    _inherit = "product.template.attribute.line"

    def write(self, values):
        res = super().write(values)
        if "value_ids" in values:
            product_image_attribute_value_ids = self.product_tmpl_id.image_ids.mapped(
                "attribute_value_ids"
            ).filtered(lambda x: x.attribute_id == self.attribute_id)
            available_attribute_values_ids = values["value_ids"][0][2] or [0]
            to_remove = product_image_attribute_value_ids.filtered(
                lambda x: x.id not in available_attribute_values_ids
            )
            if to_remove:
                for image in self.product_tmpl_id.image_ids:
                    image.attribute_value_ids -= to_remove
        return res
