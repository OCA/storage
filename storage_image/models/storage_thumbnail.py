# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from openerp import api, fields, models
import logging

_logger = logging.getLogger(__name__)

class StorageThumbnail(models.Model):
    _name = 'storage.thumbnail'
    _description = 'Storage Thumbnail'
    _inherit = 'storage.file'

    original = fields.Many2one(
        comodel_name='storage.file',
        string='Original file',
        inverse_name='thumbnail_ids',
        required=True)

    size_x = fields.Integer()
    size_y = fields.Integer()
    ratio = fields.Float()  # a quel point on a divisé
    # crop ?
    # watermarked ?
    # key_frame ?
    to_do = fields.Boolean(help='Mark as to generate from original')
