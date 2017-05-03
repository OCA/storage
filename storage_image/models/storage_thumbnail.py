# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from openerp import api, fields, models, tools
import logging

_logger = logging.getLogger(__name__)


class StorageThumbnail(models.Model):
    _name = 'storage.thumbnail'
    _description = 'Storage Thumbnail'
    _inherit = 'storage.file'

    original_id = fields.Many2one(
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


class ImageFactory(models.AbstractModel):
    _name = 'storage.image.factory'

    def persist(self, name, alt_name, blob, target):
        backend = self._deduce_backend()
        basic_data = backend.store(
            blob=blob,
            vals={},
            object_type=self.env['storage.image']
        )
        vals = self._prepare_dict(
            name=name,
            alt_name=alt_name,
            basic_data=basic_data,
            blob=blob,
            target=target)
        return self.env['storage.image'].create(vals)

    def _prepare_dict(
            self,
            name,
            basic_data,
            target,
            alt_name,
            blob,
    ):
        exifs = self._extract_exifs(blob)
        url = basic_data['url']
        file_size = basic_data['file_size']
        checksum = basic_data['checksum']
        backend_id = basic_data['backend_id']
        private_path = basic_data['private_path']
        vals = {
            'exifs': exifs,
            'name': name,
            'alt_name': alt_name,
            # TODO: refactor this
            'type': 'url',
            'url': url,
            'checksum': checksum,
            'file_size': file_size,
            'backend_id': backend_id,
            'url': url,
            'res_model': target._name,
            'res_id': target.id,
            'private_path': private_path,
        }
        return vals

    def _extract_exifs(self, kwargs):
        return ""

    def _deduce_backend(self):
        backends = self.env['storage.backend'].search([])
        return backends[0]  # par defaut on prends le premier


class ThumbnailFactory(models.AbstractModel):
    _name = 'storage.thumbnail.factory'

    def _prepare_dict(
            self,
            basic_data,
            target,
            size_x,
            size_y,
    ):
        url = basic_data['url']
        file_size = basic_data['file_size']
        checksum = basic_data['checksum']
        backend_id = basic_data['backend_id']
        private_path = basic_data['private_path']

        vals = {
            'original_id': target.file_id.id,
            'size_x': size_x,
            'size_y': size_y,
            'to_do': True,
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

    def build(self, original_id, size_x, size_y):
        # entry point !
        # a partir d'un original et d'une taille
        """
        Original_id : storage_image
        """
        blob = self.transform(
            original_id=original_id,
            size_x=size_x,
            size_y=size_y,
        )
        return self.persist(
            blob=blob,
            target=original_id,
            size_x=size_x,
            size_y=size_y)

    def transform(self, original_id, size_x, size_y):
        _logger.info('on resize !!')
        base64_source = original_id.get_base64()
        blob = tools.image_resize_image(base64_source, (size_x, size_y)) + u''
        return blob

    def persist(self, blob, target, **kwargs):
        _logger.info('on build !')
        size_x = kwargs['size_x']
        size_y = kwargs['size_y']
        backend = self.deduce_backend(target, **kwargs)
        basic_data = backend.store(blob, "file name")

        vals = self._prepare_dict(
            target=target,
            basic_data=basic_data,
            size_x=size_x,
            size_y=size_y,
        )
        _logger.info(vals)
        return self.env['storage.thumbnail'].create(vals)

    def deduce_backend(self, original, **kwargs):
        # on met kwargs ici car on peut avoir des règles metiers
        domain = []
        import pdb
        pdb.set_trace()
        if kwargs['size_x'] == 90:
            _logger.info('on est une miniature')
            domain = [('backend_type', '=', 'odoo')]

        backends = self.env['storage.backend'].search(domain)
        return backends[0]  # par defaut on prends le premier

        # autres idées
        # en fonction du type (ex : un pour les thumbnail, un autre pour image)
        # ou un pour les partner, un pour les produits ?
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
