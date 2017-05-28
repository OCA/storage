# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models
import hashlib
import logging
logger = logging.getLogger(__name__)


class OdooStorageBackend(models.Model):
    _inherit = 'storage.backend'

    backend_type = fields.Selection(
        selection_add=[('odoo', 'Odoo')])

    def _odoostore(self, vals):
        blob = vals['datas']
        checksum = u'' + hashlib.sha1(blob).hexdigest()
        name = vals.get('name', checksum)

        # res_model = OdooStrogageBackend
        # car il faut faire savoir sur quel
        # backend on est lié

        ir_attach = {
            'name': name,  # utiliser name a la place
            'type': 'binary',
            'datas': blob,
            'res_model': self._name,
            'res_id': self.id,
        }
        logger.info('on va crée le ir suivant:')
        logger.info(ir_attach)

        pj = self.env['ir.attachment'].create(ir_attach)
        size = pj.file_size
        url = (
            '/web/binary/image?model=%(res_model)s'
            '&id=%(res_id)s&field=datas'
            # comment on sait que c'est une image? a mettre ailleurs
        ) % {
            'res_model': pj._name,
            'res_id': pj.id
        }

        basic_vals = {
            # 'name': '',
            'name': name,
            'url': url,
            'file_size': size,
            'checksum': checksum,
            'backend_id': self.id,
            'private_path': pj.id
        }
        return basic_vals

    def _odooget_public_url(self, obj):
        # TODO faire mieux
        logger.info('get_public_url')
        return self._odoo_lookup(obj).url

    def _odooget_base64(self, file_id):
        logger.info('return base64 of a file')
        return self._odoo_lookup(file_id).datas

    def _odoo_lookup(self, obj):
        return self.env['ir.attachment'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('id', '=', obj.private_path)
        ])
