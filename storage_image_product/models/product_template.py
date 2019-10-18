# Copyright 2018 Akretion (http://www.akretion.com).
# @author Raphaël Reverdy <https://github.com/hparfr>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # small and medium image are here to replace
    # native image field on form and kanban
    image_small_url = fields.Char(
        related="image_ids.image_id.image_small_url", store=True
    )
    image_medium_url = fields.Char(
        related="image_ids.image_id.image_medium_url", store=True
    )
    image_ids = fields.One2many(
        "product.image.relation", inverse_name="product_tmpl_id", string="Images"
    )
