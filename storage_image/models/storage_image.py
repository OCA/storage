# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from openerp import api, fields, models
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
    _inherits = {'storage.file': 'file_id'}
    _order = 'sequence, res_model, res_id, id'

    sequence = fields.Integer(default=10)
    alt_name = fields.Char(string="Alt Image name")
    file_id = fields.Many2one('storage.file', 'File')

    thumbnail_ids = fields.One2many(
        comodel_name='storage.thumbnail',
        string='Thumbnails',
        inverse_name='res_id',
        domain=lambda self: [("res_model", "=", self._name)])

    image_medium_url = fields.Char(
        compute="_compute_image_url",
        store=True,
        readonly=True)

    image_small_url = fields.Char(
        compute="_compute_image_url",
        store=True,
        readonly=True)

    image_url = fields.Char(
        store=True,
        inverse="_inverse_image_url",
        compute="_compute_image_url")

    @api.onchange('name')
    def onchange_name(self):
        for record in self:
            if record.name:
                filename, extension = os.path.splitext(record.name)
                record.name = "%s%s" % (slugify(filename), extension)
                record.alt_name = filename
                for char in ['-', '_']:
                    record.alt_name = record.alt_name.replace(char, ' ')

    @api.multi
    def _inverse_image_url(self):
        for record in self:
            record.file_id.datas = record.image_url

    @api.model
    def create(self, vals):
        if 'backend_id' not in vals:
            vals['backend_id'] = self._deduce_backend_id()
        return super(StorageImage, self).create(vals)

    def _deduce_backend_id(self):
        """Choose the correct backend.

        By default : it's the one configured as ir.config_parameter
        Overload this method if you need something more powerfull
        """
        return int(self.env['ir.config_parameter'].get_param(
            'storage.image.backend_id'))

    def _get_medium_thumbnail(self):
        return self.get_thumbnail(128, 128)

    def _get_small_thumbnail(self):
        return self.get_thumbnail(64, 64)

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
            rec.update({
                'image_url': rec.url,
                'image_medium_url': rec._get_medium_thumbnail().url,
                'image_small_url': rec._get_small_thumbnail().url,
            })
        self.env.all.todo = todo

    @api.multi
    def get_thumbnail_from_resize(self, resize):
        self.ensure_one()
        return self.get_thumbnail(resize.size_x, resize.size_y)

    @api.multi
    def get_thumbnail(self, size_x, size_y):
        self.ensure_one()
        thumbnail = self.env['storage.thumbnail'].search([
            ('size_x', '=', size_x),
            ('size_y', '=', size_y),
            ('res_id', '=', self.id),
            ('res_model', '=', self._name),
            ])
        if not thumbnail and self.datas:
            thumbnail = self.env['storage.thumbnail']._create_thumbnail(
                self, size_x, size_y)
        return thumbnail
