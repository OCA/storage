# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class CategoryImageRelation(models.Model):
    _inherit = "category.image.relation"

    def _get_domain_for_existing_relation(self, vals):
        return [
            ("category_id", "=", vals["category_id"]),
            ("import_from_url", "=", vals["import_from_url"]),
        ]
