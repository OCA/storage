# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class StorageBackend(models.Model):
    _name = 'storage.backend'
    _inherit = 'keychain.backend'

    name = fields.Char(required=True)
    backend_type = fields.Selection([
        ('amazon-s3', 'Amazon-S3'),
        ('filestore', 'Filestore'),
        ('sftp', 'Sftp'),
        ], required=True)
    public_base_url = fields.Char()
