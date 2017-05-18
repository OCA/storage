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
        backend = self._deduce_backend()
        vals.update(backend.store(vals=vals))
        return super(StorageImage, self).create(vals)

    def _deduce_backend(self):
        """Choose the correct backend.

        By default : it's the one configured as ir.config_parameter
        Overload this method if you need something more powerfull
        """
        backend_id = int(self.env['ir.config_parameter'].get_param(
            'storage.image.backend_id'))
        return self.env['storage.backend'].browse(backend_id)

    @api.multi
    @api.depends('file_id')
    def _compute_get_image_sizes(self):
        for rec in self:
            try:
                vals = tools.image_get_resized_images(
                    rec.datas)
            except:
                vals = {"image_medium": False,
                        "image_small": False}
            rec.update(vals)

    @api.multi
    def get_thumbnails(self, size_x, size_y, multi=False):
        # faidrait filtrer sur thumbnail_ids au lieu de faire un domaine ?

        return (
            self.get_thumbnail(size_x, size_y) or
            self._ask_for_thumbnail_creation(size_x, size_y)
        )

    @api.multi
    def ask_for_thumbnail_creation(self, size_x, size_y, to_do=True):
        for img in self:
            img._ask_for_thumbnail_creation(size_x, size_y, to_do)

    def _ask_for_thumbnail_creation(self, size_x, size_y, to_do):
        kwargs = {'size_x': size_x, 'size_y': size_y, 'to_do': to_do}
        return self.env['storage.thumbnail.factory'].build(
            self, **kwargs)
