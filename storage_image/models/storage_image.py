# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from openerp import api, fields, models, tools
import logging

_logger = logging.getLogger(__name__)


class StorageImage(models.Model):
    _name = 'storage.image'
    _description = 'Storage Image'
    _inherits = {'storage.file': 'file_id'}
    _order = 'sequence, res_model, res_id, id'

    sequence = fields.Integer(default=10)
    alt_name = fields.Char(string="Alt Image name")
    # display_name = ?
    # exifs ? auteur, date de crétation, upload, gps, mots clefs, features ?

    exifs = fields.Char()

    thumbnail_ids = fields.One2many(
        comodel_name='storage.thumbnail',
        string='Thumbnails',
        inverse_name='res_id',
        domain=lambda self: [("res_model", "=", self._name)],
        #readonly=True
    )

    # a persister en base pour odoo, c'est plus simple?
    # a garder ici ou mettre dans un autre module qui étand ?
    image_medium = fields.Binary(
        compute="_compute_get_image_sizes",
        help='For backend only',
        store=True,
        readonly=True,
        # attachment=True # > 9 ?
    )
    image_small = fields.Binary(
        compute="_compute_get_image_sizes",
        help='For backend only',
        store=True,
        readonly=True,
        # attachment=True # > 9 ?
    )

    @api.model
    def create(self, vals):
        vals['res_model'] = self._context['params']['model']
        vals['res_id'] = self._context['params']['id']
        backend = self._deduce_backend()
        basic_data = backend.store(
            vals=vals
        )
        _logger.info('dans parent')
        import pdb
        pdb.set_trace()
        #vals['exifs'] = self._extract_exifs(vals['datas'])
        vals['backend_id'] = backend.id
        vals['url'] = basic_data['url']
        vals['file_size'] = basic_data['file_size']
        vals['checksum'] = basic_data['checksum']

        return super(StorageImage, self).create(vals)

    def _deduce_backend(self):
        backends = self.env['storage.backend'].search([])
        return backends[0]  # par defaut on prends le premier


    @api.multi
    @api.depends('file_id')
    def _compute_get_image_sizes(self):
        for rec in self:
            try:
                vals = tools.image_get_resized_images(
                    rec.get_base64())
            except:
                vals = {"image_medium": False,
                        "image_small": False}
            rec.update(vals)

    def get_thumbnail(self, size_x, size_y):
        # faidrait filtrer sur thumbnail_ids au lieu de faire un domaine ?
        domain = [
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('size_x', '=', size_x),
            ('size_y', '=', size_y)
        ]
        _logger.info('on va chercher du thumbnail')
        return self.env['storage.thumbnail'].search(domain)

    @api.multi
    def ask_for_thumbnail_creation(self, size_x, size_y):
        for img in self:
            img._ask_for_thumbnail_creation(size_x, size_y)

    def _ask_for_thumbnail_creation(self, size_x, size_y):
        kwargs = {'size_x': size_x, 'size_y': size_y}
        return self.env['storage.thumbnail.factory'].build(
            self, **kwargs)

    def _get_or_create(self, size_x, size_y):
        return (
            self.get_thumbnail(size_x, size_y) or
            self._ask_for_thumbnail_creation(size_x, size_y)
        )

    # def _compute_url(self):
    #     _logger.info('compute_url de l\'enfant')
    #     # TODO utile ?
    #     for rec in self:
    #         rec.file_id.public_url

    def get_base64(self):
        _logger.info('get base64 de l enfant')
        return self.file_id.get_base64()
