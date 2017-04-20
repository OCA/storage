# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from openerp import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class StorageThumbnail(models.Model):
    _name = 'storage.thumbnail'
    _description = 'Storage Thumbnail'
    _inherit = 'storage.file'

    original = fields.Many2one(
        comodel_name='storage.file',
        string='Original file',
        required=True)

    size_x = fields.Integer()
    size_y = fields.Integer()
    ratio = fields.Float()  # a quel point on a divisé
    # crop ?
    # watermarked ?
    # key_frame ?
    to_do = fields.Boolean(help='Mark as to generate from original')


class ThumbnailFactory(models.AbstractModel):
    _name = 'storage.thumbnail.factory'

    def build(self, original, **kwargs):
        _logger.info('on bulid !')
        x, y = self.deduce_size(original, **kwargs)
        backend = self.deduce_backend(original, **kwargs)
        vals = {
            'size_x': x,
            'size_y': y,
            'to_do': True,
            'backend_id': backend.id,
            'name': original.name,
            'original': original.file_id.id,
            'res_model': original._name,
            'res_id': original.id,
        }
        _logger.info(vals)
        self.env['storage.thumbnail'].create(vals)

    def deduce_backend(self, original, **kwargs):
        # on met kwargs ici car on peut avoir des règles metiers

        backends = self.env['storage.backend'].search([])
        return backends[0]  # par defaut on prends le premier

        # autres idées
        # on a une config
        backend_name = self.env['ir.config_parameter'].get_param(
            'storage.thumbnail.backend')
        return self.env['storage.backend'].search(['name', '=', backend_name])

        # ne servir du CDN qu'a partir d'une certaine taille
        if kwargs['size_x'] == 90:
            return 'local_backend'
        else:
            return 'S3'
        return True

    def deduce_size(self, original, size_x, size_y, **kwargs):
        # objectifs: renvoyer une val par defaut a size_x
        # et s'assurer un minimum de coherence
        # TODO: return min(size_x, origina.size_x)
        # size_x = size_x or original.size_x
        return size_x, size_y
