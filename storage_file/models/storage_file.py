# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class StorageFile(models.Model):
    _name = 'storage.file'
    _description = 'Storage File'

    #owner_id = fields.Integer(
    #    "Owner",
    #    required=True)
    #owner_model = fields.Char(
    #    required=True)

    path = fields.Char(help="Where the original is")
    public_url = fields.Char(compute='_compute_url')  # ou path

    name = fields.Char(required=True, help='file name')
    # mime_type = fields.Char(required=True, help='Mime type')  # ? convertion on the fly?

    size = fields.Integer(required=True, help='Size of the file in bytes')  # Optionnal ?
    sha1 = fields.Char("hash of the file")

    backend_id = fields.Many2one(
        'storage.backend',
        'Storage',
        required=True)

    meta = fields.Char()

    def _compute_url(self):
        return self.backend_id.get_public_url(self)

