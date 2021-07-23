# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def write(self, vals):
        # TODO open an issue on ODOO side
        # If you import image on an existing product
        # the field image_ids is recomputed (related field)
        # and the data inside the image_ids field is drop
        # so nothing is imported
        images = None
        if "image_ids" in vals:
            images = vals.pop("image_ids")
        super().write(vals)
        if images:
            self.product_tmpl_id.write({"image_ids": images})
        return True
