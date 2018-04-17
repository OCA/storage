# -*- coding: utf-8 -*-
# Copyright 2018 Akretion (http://www.akretion.com).
# @author Raphaël Reverdy <https://github.com/hparfr>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models
import logging

_logger = logging.getLogger(__name__)


class CategoryImage(models.Model):
    _name = "category.image"

    image_id = fields.Many2one(
        'storage.image',
    )
    category_id = fields.Many2one(
        'product.category',
    )
    image_categ_type_id = fields.Many2one(
        'category.image.type')

    # for kanban view
    image_name = fields.Char(related='image_id.name')
    # for kanban view
    image_url = fields.Char(related='image_id.image_medium_url')

    type_name = fields.Char(related='image_categ_type_id.name')


class CategoryImageType(models.Model):
    _name = 'category.image.type'

    name = fields.Char()
