# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .common import Common
from odoo.tools import config
import os
import base64


class FileStoreCase(Common):

    def setUp(self):
        super(FileStoreCase, self).setUp()
        self.backend = self.env.ref('storage_backend.default_storage_backend')

    def _get_filepath(self, filename):
        return os.path.join(
            config.filestore(self.cr.dbname),
            'storage',
            self.backend.filesystem_base_path or '',
            filename)

    def test_00_setting_datas(self):
        self.backend.store(self.filename, self.filedata, is_base64=False)
        filepath = self._get_filepath(self.filename)
        data = open(filepath, 'r').read()
        self.assertEqual(data, self.filedata)

    def test_10_getting_datas(self):
        data = self.backend.retrieve_data(self.filename)
        self.assertEqual(base64.b64decode(data), self.filedata)

    def test_20_getting_external_url(self):
        self.backend.write({
            'served_by': 'external',
            'filesystem_public_base_url': 'https://cdn.example.com',
            })
        url = self.backend.get_external_url(self.filename)
        self.assertEqual(url, 'https://cdn.example.com/test_file.txt')
