# Copyright 2020 Pharmasimple (https://www.pharmasimple.be)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ProductBrandImageRelation(models.Model):
    _inherit = "product.brand.image.relation"

    def _get_domain_for_existing_relation(self, vals):
        return [
            ("brand_id", "=", vals["brand_id"]),
            ("import_from_url", "=", vals["import_from_url"]),
        ]
