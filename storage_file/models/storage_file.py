# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class StorageFile(models.Model):
    _name = 'storage.file'
    _description = 'Storage File'
    _inherit = 'ir.attachment'

    public_url = fields.Char(compute='_compute_url')  # ou path utile ?

    backend_id = fields.Many2one(
        'storage.backend',
        'Storage',
        required=True)

    # forward compliency to v9 and v10
    checksum = fields.Char("Checksum/SHA1", size=40, select=True, readonly=True)
    mimetype = fields.Char('Mime Type', readonly=True)
    index_content = fields.Char('Indexed Content', readonly=True)
    public = fields.Boolean('Is public document')

    def _compute_url(self):
        _logger.info('compute_url du parent')
        return self.backend_id.get_public_url(self)

    def get_base64(self):
        self.backend_id.get_base64(self)
