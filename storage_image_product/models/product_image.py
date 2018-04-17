# -*- coding: utf-8 -*-
# Copyright 2018 Akretion (http://www.akretion.com).
# @author Raphaël Reverdy <https://github.com/hparfr>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class ProductImage(models.Model):
    _name = 'product.image'
    _order = 'sequence, image_id'

    sequence = fields.Integer()
    image_id = fields.Many2one(
        'storage.image',
    )
    attribute_value_ids = fields.Many2many(
        'product.attribute.value',
        string='Attributes'
    )
    available_attribute_value_ids = fields.Many2many(
        'product.attribute.value',
        string='Attributes',
        compute="_compute_available_attribute"
    )
    product_tmpl_id = fields.Many2one(
        'product.template',
    )
    # for kanban view
    image_name = fields.Char(related='image_id.name')
    # for kanban view
    image_url = fields.Char(related='image_id.image_medium_url')

    @api.depends('image_id', 'product_tmpl_id.attribute_line_ids.value_ids')
    def _compute_available_attribute(self):
        # the depend on 'image_id' only added for triggering the onchange
        for record in self:
            record.available_attribute_value_ids =\
                record.product_tmpl_id.mapped('attribute_line_ids.value_ids')
