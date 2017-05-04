# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Raph Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, tools
import logging

_logger = logging.getLogger(__name__)


class ThumbnailFactory(models.AbstractModel):
    _name = 'storage.thumbnail.factory'

    def _prepare_dict(
            self,
            basic_data,
            target,
            size_x,
            size_y,
            to_do,
    ):
        url = basic_data.get('url')
        file_size = basic_data.get('file_size')
        checksum = basic_data.get('checksum')
        backend_id = basic_data['backend_id']
        private_path = basic_data.get('private_path')

        vals = {
            'original_id': target.file_id.id,
            'size_x': size_x,
            'size_y': size_y,
            'to_do': to_do,
            # TODO: refactor this:
            'type': 'url',
            'name': target.name,
            'backend_id': backend_id,
            'url': url,
            'checksum': checksum,
            'file_size': file_size,
            'res_model': target._name,
            'res_id': target.id,
            'private_path': private_path,
        }
        return vals

    def build(self, original_id, size_x, size_y, later=False):
        # entry point !
        # a partir d'un original et d'une taille
        """
        Original_id : storage_image
        """

        if later:
            blob = None
        else:
            blob = self.transform(
                original_id=original_id,
                size_x=size_x,
                size_y=size_y,
            )

        return self.persist(
            blob=blob,
            target=original_id,
            size_x=size_x,
            size_y=size_y,
            later=later,
        )

    def transform(self, original_id, size_x, size_y):
        _logger.info('on resize !!')
        base64_source = original_id.get_base64()
        blob = tools.image_resize_image(base64_source, (size_x, size_y)) + u''
        return blob

    def persist(self, blob, target, **kwargs):
        _logger.info('on build ! %s' % kwargs['later'])
        size_x = kwargs['size_x']
        size_y = kwargs['size_y']
        later = kwargs['later']
        backend = self.deduce_backend(target, **kwargs)

        init_vals = {
            'name': self._make_name(blob=blob, target=target, **kwargs)
        }

        if later:
            basic_data = {'backend_id': backend.id}
        else:
            basic_data = backend.store(blob, init_vals)

        vals = self._prepare_dict(
            target=target,
            basic_data=basic_data,
            size_x=size_x,
            size_y=size_y,
            to_do=later,
        )
        _logger.info(vals)
        return self.env['storage.thumbnail'].create(vals)

    def _make_name(self, blob, target, **kwargs):
        """Build a name for the thumbnail"""
        return '%s_%s_%s%s' % (
            target.filename,
            kwargs['size_x'],
            kwargs['size_y'],
            target.extension
        )

    def deduce_backend(self, original, **kwargs):
        # on met kwargs ici car on peut avoir des règles metiers

        domain = [('backend_type', '=', 'sftp')]
        backends = self.env['storage.backend'].search(domain)
        return backends[0]  # par defaut on prends le premier

        # if kwargs['size_x'] == 90:
        #     _logger.info('on est une miniature')
        #     domain = [('backend_type', '=', 'odoo')]
        #
        # backends = self.env['storage.backend'].search(domain)
        # return backends[0]  # par defaut on prends le premier
        #
        # # autres idées
        # # en fonction du type (ex : un pour les thumbnail, un autre pour image)
        # # ou un pour les partner, un pour les produits ?
        # # on a une config
        # backend_name = self.env['ir.config_parameter'].get_param(
        #     'storage.thumbnail.backend')
        # return self.env['storage.backend'].search(['name', '=', backend_name])
        #
        # # ne servir du CDN qu'a partir d'une certaine taille
        # if kwargs['size_x'] == 90:
        #     return 'local_backend'
        # else:
        #     return 'S3'
        # return True

    def deduce_size(self, original, size_x, size_y, **kwargs):
        # objectifs: renvoyer une val par defaut a size_x
        # et s'assurer un minimum de coherence
        # TODO: return min(size_x, origina.size_x)
        # size_x = size_x or original.size_x
        return size_x, size_y
