# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class StorageFile(models.Model):
    _name = 'storage.file'
    _description = 'Storage File'

    owner_id = fields.Integer(
        "Owner",
        required=True)
    owner_model = fields.Char(
        required=True)
    name = fields.Char(required=True)
    url = fields.Char(compute='_compute_url')
    storage_id = fields.Many2one(
        'storage.backend',
        'Storage',
        required=True)
    meta = fields.Char()
    file_type = fields.Selection([
        ('binary', 'Binary'),
        ], required=True)
    data = fields.Binary(compute='_compute_data')

    def _compute_url(self):
        pass
        # TODO

    def _compute_data(self):
        pass
        # TODO
