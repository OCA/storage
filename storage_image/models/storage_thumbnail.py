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

    original_id = fields.Many2one(
        comodel_name='storage.file',
        string='Original file',
        help="Original image",
        required=True,
    )

    size_x = fields.Integer("weight")
    size_y = fields.Integer("height")
    # ratio = fields.Float()  # a quel point on a divisé
    # crop ?
    # watermarked ?
    # key_frame ?
    to_do = fields.Boolean(
        string="Todo",
        help='Mark as to generate from original')

    @api.model
    def create(self, vals):
        _logger.info('dans enfant, normalement on devrait faire le store ici')

        backend = self._deduce_backend()

        # TODO: trouver stroage.image dans le context
        original_id = self.env['storage.image'].browse(vals['res_id'])

        vals['res_model'] = original_id._name
        vals['res_id'] = original_id.id

        vals['name'] = self._make_name(
            vals=vals,
            target=original_id,
        )

        init_vals = {
            'size_x': vals['size_x'],
            'size_y': vals['size_y'],
            'name': vals['name'],
            'datas': original_id.datas,
        }

        if vals['to_do']:
            basic_data = {'backend_id': backend.id}
        else:
            basic_data = backend.store(init_vals)

        vals['url'] = basic_data.get('url')
        vals['file_size'] = basic_data.get('file_size')
        vals['checksum'] = basic_data.get('checksum')
        vals['backend_id'] = basic_data['backend_id']
        vals['private_path'] = basic_data.get('private_path')
        vals['original_id'] = original_id.file_id.id
        vals['url'] = 'url'

        return super(StorageThumbnail, self).create(vals)

    def _deduce_backend(self, **kwargs):
        domain = [('backend_type', '=', 'sftp')]
        backends = self.env['storage.backend'].search(domain)
        return backends[0]  # par defaut on prends le premier

    def _make_name(self, vals, target):
        """Build a name for the thumbnail"""
        return '%s_%s_%s%s' % (
            target.filename,
            vals['size_x'],
            vals['size_y'],
            target.extension
        )
