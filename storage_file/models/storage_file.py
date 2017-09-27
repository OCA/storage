# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
import base64
import logging
import os
import mimetypes
import hashlib
from openerp.exceptions import Warning as UserError
from openerp.tools.translate import _
_logger = logging.getLogger(__name__)


class StorageFile(models.Model):
    _name = 'storage.file'
    _description = 'Storage File'

    name = fields.Char(
        required=True,
        select=True)
    backend_id = fields.Many2one(
        'storage.backend',
        'Storage',
        select=True,
        required=True)
    url = fields.Char(help="HTTP accessible path for odoo backend to the file")
    private_path = fields.Char(help='Location for backend, may be relative')
    res_model = fields.Char(
        readonly=False,
        select=True)
    res_id = fields.Integer(
        readonly=False,
        select=True)
    file_size = fields.Integer('File Size')
    human_file_size = fields.Char(
        'Human File Size',
        compute='_compute_human_file_size',
        store=True)
    checksum = fields.Char(
        "Checksum/SHA1",
        size=40,
        select=True,
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
        ('path_uniq', 'unique(private_path, backend_id)',
         'The private path must be uniq per backend'),
    ]

    # TODO add code for using security rule like ir.attachment

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
        suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
        for record in self:
            suffix_index = 0
            size = record.file_size
            while size > 1024 and suffix_index < 4:
                suffix_index += 1
                size = size/1024.0
            record.human_file_size = "%.*f%s" % (
                2, size, suffixes[suffix_index])

    def _prepare_meta_for_file(self, datas):
        return {
            'url': self.backend_id.sudo().get_public_url(private_path),
            'checksum': hashlib.sha1(datas).hexdigest(),
            'file_size': len(datas),
            'private_path': private_path
            }

    @api.multi
    def _inverse_datas(self):
        for record in self:
            b_decoded = base64.b64decode(record.datas)
            private_path = self.backend_id.sudo().store(
                record.name,
                b_decoded,
                is_public=True,
                is_base64=False)
            vals = record._prepare_meta_for_file(b_decoded, private_path)
            record.write(vals)

    @api.multi
    def _compute_datas(self):
        for rec in self:
            if not rec.url:
                rec.datas = None
            else:
                try:
                    rec.datas = rec.backend_id.sudo().retrieve_datas(
                        rec.private_path)
                except:
                    _logger.error('Image %s not found', rec.url)
                    rec.datas = None
                    raise

    @api.depends('name')
    def _compute_extract_filename(self):
        for rec in self:
            rec.filename, rec.extension = os.path.splitext(rec.name)
            mime, enc = mimetypes.guess_type(rec.name)
            rec.mimetype = mime
