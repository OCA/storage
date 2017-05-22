# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from openerp import api, fields, models
from openerp.tools import image_resize_image
import logging
_logger = logging.getLogger(__name__)


class StorageThumbnail(models.Model):
    _name = 'storage.thumbnail'
    _description = 'Storage Thumbnail'
    _inherits = {'storage.file': 'file_id'}

    size_x = fields.Integer("weight")
    size_y = fields.Integer("height")
    file_id = fields.Many2one('storage.file', 'File')

    def _prepare_thumbnail(self, image, size_x, size_y):
        return {
            'res_model': image._name,
            'res_id': image.id,
            'name' : '%s_%s_%s%s' % (image.filename, size_x, size_y, image.extension),
            'size_x': size_x,
            'size_y': size_y,
            }

    def _resize(self, image, size_x, size_y):
        return image_resize_image(image.datas, size=(size_x, size_y))

    def _create_thumbnail(self, image, size_x, size_y):
        vals = self._prepare_thumbnail(image, size_x, size_y)
        vals['datas'] = self._resize(image, size_x, size_y)
        print 'create thumbnail'
        return self.create(vals)

    def _deduce_backend(self):
        """Choose the correct backend.

        By default : it's the one configured as ir.config_parameter
        Overload this method if you need something more powerfull
        """
        backend_id = int(self.env['ir.config_parameter'].get_param(
            'storage.image.backend_id'))
        return self.env['storage.backend'].browse(backend_id)

    @api.model
    def create(self, vals):
        backend = self._deduce_backend()
        vals.update(backend.store(vals=vals))
        return super(StorageThumbnail, self).create(vals)
