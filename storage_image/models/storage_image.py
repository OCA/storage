# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from openerp import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class StorageImage(models.Model):
    _name = 'storage.image'
    _description = 'Storage Image'
    _inherits = {'storage.file': 'file_id'}

    alt_name = fields.Char(string="Alt Image name")
    # display_name = ?
    # exifs ? auteur, date de crétation, upload, gps, mots clefs, features ?

    exifs = fields.Char()

    thumbnail_ids = fields.One2many(
        comodel_name='storage.thumbnail',
        string='Thumbnails',
        inverse_name='original',
        domain=lambda self: [("res_model", "=", self._name)],
    )

    def get_thumbnail(self, size_x, size_y):
        # faidrait filtrer sur thumbnail_ids au lieu de faire un domaine ?
        domain = [
            ('res_model', '=', self._name),
            ('id', '=', self.id),
            ('size_x', '=', size_x),
            ('size_y', '=', size_y)
        ]
        return self.env['storage.thumbnail'].search(domain)

    @api.multi
    def ask_for_thumbnail_creation(self, size_x, size_y):
        for img in self:
            vals = {
                'size_x': size_x,
                'size_y': size_y,
                'res_model': img._name,
                'res_id': img.id,
                'to_do': True
            }
            self.env['storage.thumbnail'].create(vals)

    def _compute_url(self):
        _logger.info('compute_url de l\'enfant')
        return self.file_id.backend_id.get_public_url(self)

