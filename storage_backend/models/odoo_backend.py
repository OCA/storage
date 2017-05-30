# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models
import hashlib
import base64


import logging
logger = logging.getLogger(__name__)


class OdooStorageBackend(models.Model):
    _inherit = 'storage.backend'

    backend_type = fields.Selection(
        selection_add=[('odoo', 'Odoo')])

    def _odoo_store(self, name, datas, is_public=False, **kwargs):
        checksum = u'' + hashlib.sha1(datas).hexdigest()
        name = name or checksum
        datas_encoded = base64.b64encode(datas)
        ir_attach_vals = {
            'name': name,
            'type': 'binary',
            'datas': datas_encoded,
        }
        logger.info('on va crée le ir suivant:')
        logger.info(ir_attach_vals)

        attachment = self.env['ir.attachment'].create(ir_attach_vals)
        return attachment.id

    def _odooget_public_url(self, attach_id):
        # TODO faire mieux
        logger.info('get_public_url')
#        attach = self.env['ir.attachment'].search([('name', '=', name)],
#            limit=1)
        attach = self.env['ir.attachment'].browse(attach_id)
        url = (
            '/web/binary/image?model=%(model)s'
            '&id=%(attach_id)s&field=datas'
            # comment on sait que c'est une image? a mettre ailleurs
        ) % {
            'model': attach._name,
            'attach_id': attach.id
        }
        print url
        return url

    def _odooget_base64(self, file_id):
        logger.info('return base64 of a file')
        return self._odoo_lookup(file_id).datas

    def _odoo_lookup(self, obj):
        return self.env['ir.attachment'].search([
            ('id', '=', obj.private_path)
        ])
