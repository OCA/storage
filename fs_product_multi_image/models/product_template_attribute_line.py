# Copyright 2023 ACSONE SA/NV
# Copyright 2017 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ProductTemplateAttributeLine(models.Model):

    _inherit = "product.template.attribute.line"

    def write(self, values):
        res = super().write(values)
        if "value_ids" in values:
            product_image_attribute_value_ids = self.product_tmpl_id.image_ids.mapped(
                "attribute_value_ids"
            ).filtered(lambda x: x.attribute_id == self.attribute_id)
            available_attribute_values_ids = self.value_ids
            to_remove = product_image_attribute_value_ids.filtered(
                lambda x: x not in available_attribute_values_ids
            )
            if to_remove:
                for image in self.product_tmpl_id.image_ids:
                    image.attribute_value_ids -= to_remove
        return res

    def unlink(self):
        for line in self:
            for image in line.product_tmpl_id.image_ids:
                image.attribute_value_ids -= line.value_ids
        return super().unlink()
