# Copyright 2018 Akretion (http://www.akretion.com).
# @author Raphaël Reverdy <https://github.com/hparfr>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # small and medium image are here to replace
    # native image field on form and kanban
    image_small_url = fields.Char(compute="_compute_image_urls", store=True)
    image_medium_url = fields.Char(compute="_compute_image_urls", store=True)
    image_ids = fields.One2many(
        "product.image.relation", inverse_name="product_tmpl_id", string="Images"
    )

    @api.depends("image_ids", "image_ids.sequence", "image_ids.image_id")
    def _compute_image_urls(self):
        for template in self:
            template_images = template.image_ids.sorted(
                key=lambda i: (i.sequence, i.image_id)
            )
            if template_images:
                template.image_small_url = template_images[0].image_id.image_small_url
                template.image_medium_url = template_images[0].image_id.image_medium_url
            else:
                template.image_small_url = None
                template.image_medium_url = None
