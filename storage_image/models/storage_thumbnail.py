# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from openerp import fields, models
import logging

_logger = logging.getLogger(__name__)


class StorageThumbnail(models.Model):
    _name = 'storage.thumbnail'
    _description = 'Storage Thumbnail'
    _inherit = 'storage.file'

    original_id = fields.Many2one(
        comodel_name='storage.file',
        string='Original file',
        help="Original image",
        required=True)

    size_x = fields.Integer("weight")
    size_y = fields.Integer("height")
    # ratio = fields.Float()  # a quel point on a divisé
    # crop ?
    # watermarked ?
    # key_frame ?
    to_do = fields.Boolean(
        string="Todo",
        help='Mark as to generate from original')
