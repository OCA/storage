# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from openerp import api, fields, models


class ThumbnailOwner(models.AbstractModel):
    _name = 'thumbnail.owner'
    _description = 'Thumbnail Owner'

    thumbnail_ids = fields.One2many(
        comodel_name='storage.thumbnail',
        string='Thumbnails',
        inverse_name='res_id',
        domain=lambda self: [("res_model", "=", self._name)])
    image_medium_url = fields.Char(
        compute="_compute_image_url",
        readonly=True)
    image_small_url = fields.Char(
        compute="_compute_image_url",
        readonly=True)

    def _get_medium_thumbnail(self):
        return self.get_thumbnail(128, 128)

    def _get_small_thumbnail(self):
        return self.get_thumbnail(64, 64)

    @api.multi
    def get_thumbnail(self, size_x, size_y):
        self.ensure_one()
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

    @api.multi
    @api.depends('url')
    def _compute_image_url(self):
        # We need a clear env for getting the thumbnail
        # as a potential create/write can be called
        # This avoid useless recomputation of field
        # TODO we should see with odoo how we can improve the ORM
        todo = self.env.all.todo
        self.env.all.todo = {}
        for rec in self:
            if rec.url:
                medium_url = rec.sudo()._get_medium_thumbnail().url
                small_url = rec.sudo()._get_small_thumbnail().url
                rec.image_medium_url = medium_url
                rec.image_small_url = small_url
        self.env.all.todo = todo
