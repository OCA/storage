# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models
import base64


import logging
logger = logging.getLogger(__name__)


class OdooStorageBackend(models.Model):
    _inherit = 'storage.backend'

    backend_type = fields.Selection(
        selection_add=[('odoo', 'Odoo')])

    def _odoo_store(self, name, datas, is_public=False, **kwargs):
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
            'web/binary/image?model=%(model)s'
            '&id=%(attach_id)s&field=datas'
            # comment on sait que c'est une image? a mettre ailleurs
        ) % {
            'model': attach._name,
            'attach_id': attach.id
        }
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        if not base_url.endswith('/'):
            base_url = base_url + '/'
        return base_url + url

    # This method is kind of useless but we can keep it to be consistent with
    # other storage backends
    def _odoo_retrieve_data(self, attach_id):
        logger.info('return base64 of a file')
        attach = self.env['ir.attachment'].browse(attach_id)
        return attach.datas
