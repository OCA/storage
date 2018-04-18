# -*- coding: utf-8 -*-
# Copyright 2018 Akretion (http://www.akretion.com).
# @author Raphaël Reverdy <https://github.com/hparfr>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class ImageTag(models.Model):
    _name = 'image.tag'

    name = fields.Char()
    apply_on = fields.Selection(
        selection=[
            ('product', 'Product'),
            ('category', 'Category'),
            ])
