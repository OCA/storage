# -*- coding: utf-8 -*-
# Copyright 2018 Akretion (http://www.akretion.com).
# @author Raphaël Reverdy <https://github.com/hparfr>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    image_small_url = fields.Char(
        related='image_ids.image_id.image_small_url')
    image_medium_url = fields.Char(
        related='image_ids.image_id.image_medium_url')
    image_ids = fields.One2many(
        'product.image',
        inverse_name='product_tmpl_id',
    )
