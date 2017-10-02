# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ImageResize(models.Model):
    _name = 'image.resize'
    _description = 'Image Resize'
    _rec_name = "display_name"

    name = fields.Char(required=True)
    key = fields.Char(required=True)
    size_x = fields.Integer(required=True)
    size_y = fields.Integer(required=True)
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True)

    @api.depends('name', 'size_x', 'size_y')
    def _compute_display_name(self):
        for record in self:
            record.display_name = '%s (%sx%s)' % (
                record.name, record.size_x, record.size_y)
