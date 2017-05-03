# -*- coding: utf-8 -*-

import logging
from openerp import models, fields, api

_logger = logging.getLogger(__name__)

class StorageThumbnailWizard(models.TransientModel):
    _name = "storage.thumbnail.wizard"

    size_x = fields.Integer('Size X')
    size_y = fields.Integer('Size Y')

    @api.multi
    def create_thumb(self):
        self.ensure_one()

        active_id = self._context['active_id']
        active_model = self._context['active_model']
        original_id = self.env[active_model].browse(active_id)

        img = self.env['storage.thumbnail.factory'].build(
            size_x=self.size_x,
            size_y=self.size_y,
            original_id=original_id)

        return True
