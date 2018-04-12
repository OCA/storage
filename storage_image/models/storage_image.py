# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models
import logging
import os

_logger = logging.getLogger(__name__)

try:
    from slugify import slugify
except ImportError:
    _logger.debug('Cannot `import slugify`.')


class StorageImage(models.Model):
    _name = 'storage.image'
    _description = 'Storage Image'
    _inherit = 'thumbnail.mixin'
    _inherits = {'storage.file': 'file_id'}

    alt_name = fields.Char(string="Alt Image name")
    file_id = fields.Many2one(
        'storage.file',
        'File',
        required=True,
        ondelete='cascade')

    @api.onchange('name')
    def onchange_name(self):
        for record in self:
            if record.name:
                filename, extension = os.path.splitext(record.name)
                record.name = "%s%s" % (slugify(filename), extension)
                record.alt_name = filename
                for char in ['-', '_']:
                    record.alt_name = record.alt_name.replace(char, ' ')

    @api.model
    def create(self, vals):
        if 'backend_id' not in vals:
            vals['backend_id'] = self._get_backend_id()
        if 'image_medium_url' in vals:
            vals['data'] = vals.pop('image_medium_url')
        image = super(StorageImage, self).create(vals)
        return image

    def _get_backend_id(self):
        """Choose the correct backend.

        By default : it's the one configured as ir.config_parameter
        Overload this method if you need something more powerfull
        """
        return int(self.env['ir.config_parameter'].get_param(
            'storage.image.backend_id'))
