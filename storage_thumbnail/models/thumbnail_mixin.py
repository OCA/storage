# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from openerp import api, fields, models


class ThumbnailMixing(models.AbstractModel):
    _name = 'thumbnail.mixin'
    _description = 'Thumbnail Mixin add the thumbnail capability'

    thumbnail_ids = fields.One2many(
        comodel_name='storage.thumbnail',
        string='Thumbnails',
        inverse_name='res_id',
        domain=lambda self: [("res_model", "=", self._name)])
    image_medium_url = fields.Char(readonly=True)
    image_small_url = fields.Char(readonly=True)

    def _get_medium_thumbnail(self):
        return self.get_or_create_thumbnail(128, 128)

    def _get_small_thumbnail(self):
        return self.get_or_create_thumbnail(64, 64)

    def get_or_create_thumbnail(self, size_x, size_y):
        self.ensure_one()
        self = self.with_context(bin_size=False)
        thumbnail = self.env['storage.thumbnail'].search([
            ('size_x', '=', size_x),
            ('size_y', '=', size_y),
            ('res_id', '=', self.id),
            ('res_model', '=', self._name),
        ])
        if not thumbnail and self.data:
            thumbnail = self.env['storage.thumbnail']._create_thumbnail(
                self, size_x, size_y)
        return thumbnail

    def generate_odoo_thumbnail(self):
        self.write({
            'image_medium_url': self.sudo()._get_medium_thumbnail().url,
            'image_small_url': self.sudo()._get_small_thumbnail().url,
            })
        return True

    @api.model
    def create(self, vals):
        record = super(ThumbnailMixing, self).create(vals)
        record.generate_odoo_thumbnail()
        return record
