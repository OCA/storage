# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Raph Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models
import logging

_logger = logging.getLogger(__name__)


class ImageFactory(models.AbstractModel):
    _name = 'storage.image.factory'

    def persist(self, name, alt_name, blob, target):
        backend = self._deduce_backend()
        init_vals = {'name': name, 'alt_name': alt_name}
        basic_data = backend.store(
            blob=blob,
            vals=init_vals,
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
