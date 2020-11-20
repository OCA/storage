# -*- coding: utf-8 -*-
# Copyright 2018 Akretion (http://www.akretion.com).
# @author Raphaël Reverdy <https://github.com/hparfr>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class CategoryImageRelation(models.Model):
    _name = "category.image.relation"
    _inherit = "image.relation.abstract"

    category_id = fields.Many2one("product.category")
    tag_id = fields.Many2one("image.tag", domain=[("apply_on", "=", "category")])


class ImageTag(models.Model):
    _name = "image.tag"

    name = fields.Char()
