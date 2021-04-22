# Copyright 2018 Akretion (http://www.akretion.com).
# @author Raphaël Reverdy <https://github.com/hparfr>
# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    image_ids = fields.One2many(
        comodel_name="product.image.relation",
        inverse_name="product_tmpl_id",
        string="Images",
    )
    main_image_id = fields.Many2one(
        comodel_name="storage.image",
        compute="_compute_main_image_id",
        # Store it to improve perf on product views
        store=True,
    )
    # small and medium image are here to replace
    # native image field on form and kanban
    image_small_url = fields.Char(related="main_image_id.image_small_url")
    image_medium_url = fields.Char(related="main_image_id.image_medium_url")

    @api.depends("image_ids", "image_ids.sequence", "image_ids.image_id")
    def _compute_main_image_id(self):
        for record in self:
            record.main_image_id = record._get_main_image()

    def _get_main_image(self):
        return fields.first(
            self.image_ids.sorted(key=lambda i: (i.sequence, i.image_id))
        ).image_id
