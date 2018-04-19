# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # small and medium image are here to replace
    # native image field on form and kanban
    variant_image_small_url = fields.Char(
        related='variant_image_ids.image_id.image_small_url')
    variant_image_medium_url = fields.Char(
        related='variant_image_ids.image_id.image_medium_url')
    variant_image_ids = fields.Many2many(
        'product.image',
        compute="_compute_variant_image_ids")

    @api.depends('product_tmpl_id.image_ids', 'attribute_value_ids')
    def _compute_variant_image_ids(self):
        for variant in self:
            res = self.env['product.image'].browse([])
            for image in variant.image_ids:
                if not (image.attribute_value_ids -
                        variant.attribute_value_ids):
                    res |= image
            variant.variant_image_ids = res
