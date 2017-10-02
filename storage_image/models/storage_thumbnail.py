# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models
from odoo.tools import image_resize_image
import logging
_logger = logging.getLogger(__name__)


class StorageThumbnail(models.Model):
    _name = 'storage.thumbnail'
    _description = 'Storage Thumbnail'
    _inherits = {'storage.file': 'file_id'}

    size_x = fields.Integer("weight")
    size_y = fields.Integer("height")
    file_id = fields.Many2one(
        'storage.file',
        'File',
        required=True,
        ondelete='cascade')

    def _prepare_thumbnail(self, image, size_x, size_y):
        return {
            'res_model': image._name,
            'res_id': image.id,
            'name': '%s_%s_%s%s' % (
                image.filename, size_x, size_y, image.extension),
            'size_x': size_x,
            'size_y': size_y,
            }

    def _resize(self, image, size_x, size_y):
        return image_resize_image(image.datas, size=(size_x, size_y))

    def _create_thumbnail(self, image, size_x, size_y):
        vals = self._prepare_thumbnail(image, size_x, size_y)
        datas = self._resize(image, size_x, size_y)
        record = self.create(vals)
        # Bug with odoo 8 the field datas belong to the storage.file
        # and the _create method never write it as it's a computed field
        # with the new api and it's an inherited fields
        record.file_id.write({'datas': datas})
        return record

    def _deduce_backend_id(self):
        """Choose the correct backend.

        By default : it's the one configured as ir.config_parameter
        Overload this method if you need something more powerfull
        """
        return int(self.env['ir.config_parameter'].get_param(
            'storage.image.backend_id'))

    @api.model
    def create(self, vals):
        vals['backend_id'] = self._deduce_backend_id()
        return super(StorageThumbnail, self).create(vals)
