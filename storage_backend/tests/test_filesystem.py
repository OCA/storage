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
            self.backend.directory_path or '',
            filename)

    def test_00_setting_and_getting_data_from_root(self):
        self.backend.add_b64_data(self.filename, self.filedata)
        filepath = self._get_filepath(self.filename)
        data = open(filepath, 'r').read()
        self.assertEqual(data, base64.b64decode(self.filedata))
        data = self.backend.get_b64_data(self.filename)
        self.assertEqual(data, self.filedata)

    def test_00_setting_and_getting_data_from_dir(self):
        self.backend.directory_path = 'subdirectory/here'
        self.backend.add_b64_data(self.filename, self.filedata)
        filepath = self._get_filepath(self.filename)
        data = open(filepath, 'r').read()
        self.assertEqual(data, base64.b64decode(self.filedata))
        data = self.backend.get_b64_data(self.filename)
        self.assertEqual(data, self.filedata)
