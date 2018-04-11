# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.tests.common import TransactionComponentCase
import base64


class GenericStoreCase(object):

    def _test_setting_and_getting_data(self):
        self.backend.add_b64_data(
            self.filename, self.filedata, mimetype=u'text/plain')
        data = self.backend.get_b64_data(self.filename)
        self.assertEqual(data, self.filedata)

    def test_setting_and_getting_data_from_root(self):
        self._test_setting_and_getting_data()

    def test_setting_and_getting_data_from_dir(self):
        self.backend.directory_path = self.case_with_subdirectory
        self._test_setting_and_getting_data()


class Common(TransactionComponentCase):

    def setUp(self):
        super(Common, self).setUp()
        self.backend = self.env.ref('storage_backend.default_storage_backend')
        self.filedata = base64.b64encode('This is a simple file')
        self.filename = 'test_file.txt'
        self.case_with_subdirectory = 'subdirectory/here'
