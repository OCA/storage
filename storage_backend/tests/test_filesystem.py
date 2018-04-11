# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .common import Common, GenericStoreCase
from odoo.tools import config
import os
import base64


class FileSystemCase(Common, GenericStoreCase):

    def _get_filepath(self, filename):
        return os.path.join(
            config.filestore(self.cr.dbname),
            'storage',
            self.backend.directory_path or '',
            filename)

    def _check_file_on_filestore(self):
        filepath = self._get_filepath(self.filename)
        data = open(filepath, 'r').read()
        self.assertEqual(data, base64.b64decode(self.filedata))

    def test_setting_and_getting_data_from_root(self):
        super(FileSystemCase, self).test_setting_and_getting_data_from_root()
        self._check_file_on_filestore()

    def test_setting_and_getting_data_from_dir(self):
        super(FileSystemCase, self).test_setting_and_getting_data_from_dir()
        self._check_file_on_filestore()
