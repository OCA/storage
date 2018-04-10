# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
import base64
import logging
import os
import mimetypes
import hashlib
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.tools import human_size
_logger = logging.getLogger(__name__)


class StorageFile(models.Model):
    _name = 'storage.file'
    _description = 'Storage File'

    name = fields.Char(required=True, index=True)
    backend_id = fields.Many2one(
        'storage.backend',
        'Storage',
        index=True,
        required=True)
    url = fields.Char(
        readonly=True,
        help="HTTP accessible path for odoo backend to the file")
    relative_path = fields.Char(
        readonly=True,
        help='Relative location for backend')
    file_size = fields.Integer('File Size')
    human_file_size = fields.Char(
        'Human File Size',
        compute='_compute_human_file_size',
        store=True)
    checksum = fields.Char(
        "Checksum/SHA1",
        size=40,
        index=True,
        readonly=True)
    filename = fields.Char(
        "Filename without extension",
        compute='_compute_extract_filename',
        store=True)
    extension = fields.Char(
        "Extension",
        compute='_compute_extract_filename',
        store=True)
    mimetype = fields.Char(
        "Mime Type",
        compute='_compute_extract_filename',
        store=True)
    datas = fields.Binary(
        help="Datas",
        inverse='_inverse_datas',
        compute='_compute_datas',
        store=False)

    _sql_constraints = [
        ('url_uniq', 'unique(url)', 'The url must be uniq'),
        ('path_uniq', 'unique(relative_path, backend_id)',
         'The private path must be uniq per backend'),
    ]

    @api.multi
    def write(self, vals):
        if 'datas' in vals:
            for record in self:
                if record.datas:
                    raise UserError(
                        _('File can not be updated,'
                          'remove it and create a new one'))
        return super(StorageFile, self).write(vals)

    @api.depends('file_size')
    def _compute_human_file_size(self):
        for record in self:
            record.human_file_size = human_size(self.file_size)

    def _build_relative_path(self, checksum):
        self.ensure_one()
        if not self.backend_id.filename_strategy:
            raise UserError(_(
                "The filename strategy is empty for the backend %s.\n"
                "Please configure it") % self.backend_id.name)
        if self.backend_id.filename_strategy == 'hash':
            return checksum[:2] + '/' + checksum
        elif self.backend_id.filename_strategy == 'name_with_id':
            return "%s-%s%s" % (self.filename, self.id, self.extension)

    def _prepare_meta_for_file(self):
        bin_data = base64.b64decode(self.datas)
        checksum = hashlib.sha1(bin_data).hexdigest()
        relative_path = self._build_relative_path(checksum)
        if self.backend_id.served_by == 'odoo':
            base_url = self.env['ir.config_parameter'].sudo()\
                .get_param('web.base.url')
            url = base_url + '/web/content/storage.file/%s/datas' % self.id
        else:
            url = self.backend_id.sudo().get_external_url(relative_path)
        return {
            'url': url,
            'checksum': checksum,
            'file_size': len(bin_data),
            'relative_path': relative_path
            }

    @api.multi
    def _inverse_datas(self):
        for record in self:
            record.write(record._prepare_meta_for_file())
            record.backend_id.sudo().store(record.relative_path, record.datas)

    @api.multi
    def _compute_datas(self):
        for rec in self:
            if self._context.get('bin_size'):
                rec.datas = rec.file_size
            elif rec.relative_path:
                rec.datas = rec.backend_id.sudo().retrieve_data(
                    rec.relative_path)
            else:
                rec.datas = None

    @api.depends('name')
    def _compute_extract_filename(self):
        for rec in self:
            rec.filename, rec.extension = os.path.splitext(rec.name)
            mime, enc = mimetypes.guess_type(rec.name)
            rec.mimetype = mime
