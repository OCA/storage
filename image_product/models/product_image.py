# -*- coding: utf-8 -*-
# Copyright 2018 Akretion (http://www.akretion.com).
# @author Raphaël Reverdy <https://github.com/hparfr>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models
import logging

_logger = logging.getLogger(__name__)


class ProductImage(models.Model):
    _name = 'product.image'

    image_id = fields.Many2one(
        'storage.image',
    )
    attribute_value_ids = fields.Many2many(
        'product.attribute.value',
        string='Attributes'
    )
    product_tmpl_id = fields.Many2one(
        'product.template',
    )
    # for kanban view
    image_name = fields.Char(related='image_id.name')
    # for kanban view
    image_url = fields.Char(related='image_id.image_medium_url')
