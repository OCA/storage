# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import Warning as UserError
import urllib, base64
import logging
import os
import mimetypes
import hashlib
_logger = logging.getLogger(__name__)

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO


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
        store=False)  #

    def _prepare_meta_for_file(self, datas):
        return {
            'url': self.backend_id.get_public_url(self.name),
            'checksum': hashlib.sha1(datas).hexdigest(),
            'file_size': len(datas),
            }

    @api.multi
    def _inverse_datas(self):
        for record in self:
            b_decoded = base64.b64decode(record.datas)
            self.backend_id.store(
                record.name,
                b_decoded,
                is_public=True,
                is_base64=False)
            vals = record._prepare_meta_for_file(b_decoded)
            record.write(vals)

    @api.multi
    def _compute_datas(self):
        for rec in self:
            try:
                rec.datas = base64.b64encode(urllib.urlopen(rec.url).read())
            except:
                _logger.error('Image %s not found', rec.url)
                rec.datas = None

    @api.depends('name')
    def _compute_extract_filename(self):
        for rec in self:
            rec.filename, rec.extension = os.path.splitext(rec.name)
            mime, enc = mimetypes.guess_type(rec.name)
            rec.mimetype = mime
