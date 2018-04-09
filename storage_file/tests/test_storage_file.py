# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.tests.common import TransactionComponentCase
import base64
import urlparse
from odoo.exceptions import UserError


class StorageFileCase(TransactionComponentCase):

    def setUp(self):
        super(StorageFileCase, self).setUp()
        self.backend = self.env.ref('storage_backend.default_storage_backend')
        data = 'This is a simple file'
        self.filesize = len(data)
        self.filedata = base64.b64encode(data)
        self.filename = 'test_file.txt'

    def _create_storage_file(self):
        return self.env['storage.file'].create({
            'name': self.filename,
            'backend_id': self.backend.id,
            'datas': self.filedata,
            })

    def test_create_and_read_served_by_odoo(self):
        stfile = self._create_storage_file()
        self.assertEqual(stfile.datas, self.filedata)
        self.assertEqual(stfile.mimetype, u'text/plain')
        self.assertEqual(stfile.extension, u'.txt')
        self.assertEqual(stfile.filename, u'test_file')
        url = urlparse.urlparse(stfile.url)
        self.assertEqual(
            url.path,
            "/web/content/storage.file/%s/datas" % stfile.id)
        self.assertEqual(stfile.file_size, self.filesize)

    def test_create_and_read_served_by_external(self):
        self.backend.write({
            'served_by': 'external',
            'filesystem_public_base_url': 'https://cdn.example.com',
            })
        stfile = self._create_storage_file()
        self.assertEqual(stfile.datas, self.filedata)
        self.assertEqual(stfile.url, 'https://cdn.example.com/test_file.txt')
        self.assertEqual(stfile.file_size, self.filesize)

    def test_read_bin_size(self):
        stfile = self._create_storage_file()
        self.assertEqual(
            stfile.with_context(bin_size=True).datas,
            '21.00 bytes')

    def test_cannot_update_datas(self):
        stfile = self._create_storage_file()
        datas = base64.b64encode('This is different datas')
        with self.assertRaises(UserError):
            stfile.write({'datas': datas})

        # check that the file have been not modified
        self.assertEqual(stfile.read()[0]['datas'], self.filedata)
