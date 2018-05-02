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
    url_key = fields.Char(
        "Url key",
        help="Specific URL key for generating the url of the image",
    )
    file_id = fields.Many2one(
        'storage.file',
        'File',
        required=True,
        ondelete='cascade')
    res_model = fields.Char(
        readonly=False,
        index=True)
    res_id = fields.Integer(
        readonly=False,
        index=True)

    def _prepare_thumbnail(self, image, size_x, size_y, url_key):
        return {
            'data': self._resize(image, size_x, size_y),
            'res_model': image._name,
            'res_id': image.id,
            'name': '%s_%s_%s%s' % (
                url_key or image.filename,
                size_x,
                size_y,
                image.extension),
            'size_x': size_x,
            'size_y': size_y,
            'url_key': url_key,
        }

    def _resize(self, image, size_x, size_y):
        return image_resize_image(image.data, size=(size_x, size_y))

    def _create_thumbnail(self, image, size_x, size_y, url_key):
        vals = self._prepare_thumbnail(image, size_x, size_y, url_key)
        return self.create(vals)

    def _get_backend_id(self):
        """Choose the correct backend.

        By default : it's the one configured as ir.config_parameter
        Overload this method if you need something more powerfull
        """
        return int(self.env['ir.config_parameter'].get_param(
            'storage.thumbnail.backend_id'))

    @api.model
    def create(self, vals):
        vals.update({
            'backend_id': self._get_backend_id(),
            'file_type': 'thumbnail',
            })
        return super(StorageThumbnail, self).create(vals)

    def unlink(self):
        files = self.mapped('file_id')
        result = super(StorageThumbnail, self).unlink()
        files.unlink()
        return result
