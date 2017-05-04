# -*- coding: utf-8 -*-

import logging
from openerp import models, fields, api

_logger = logging.getLogger(__name__)


class StorageImageWizard(models.TransientModel):
    _name = "storage.image.wizard"

    name = fields.Char('Name')
    alt_name = fields.Char('Alt name')
    the_file = fields.Binary()

    @api.multi
    def associate(self):
        self.ensure_one()

        active_id = self._context['active_id']
        active_model = self._context['active_model']
        target = self.env[active_model].browse(active_id)

        img = self.env['storage.image.factory'].persist(
            name=self.name,
            alt_name=self.alt_name,
            blob=self.the_file,
            target=target)

        return img
