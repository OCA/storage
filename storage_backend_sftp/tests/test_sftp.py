# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# pylint: disable=missing-manifest-dependency
# disable warning on 'vcr' missing in manifest: this is only a dependency for
# dev/tests

from odoo.addons.storage_backend.tests.common import Common
import os
import logging
_logger = logging.getLogger(__name__)


class SftpCase(Common):

    def setUp(self):
        super(SftpCase, self).setUp()
        self.backend = self.env.ref('storage_backend.default_storage_backend')
        self.backend.write({
            'backend_type': 'sftp',
            'sftp_login': 'foo',
            'sftp_password': 'pass',
            'sftp_server': os.environ.get('SFTP_HOST', 'localhost'),
            'sftp_port': os.environ.get('SFTP_PORT', '2222'),
            'directory_path': 'upload',
            })

    def test_00_setting_and_reading_data_from_root(self):
        self.backend.add_b64_data(
            self.filename, self.filedata, mimetype=u'text/plain')
        data = self.backend.get_b64_data(self.filename)
        self.assertEqual(data, self.filedata)

    def test_10_setting_and_reading_data_from_directory(self):
        self.backend.directory_path = 'upload/subdirectory/here'
        self.backend.add_b64_data(
            self.filename, self.filedata, mimetype=u'text/plain')
        data = self.backend.get_b64_data(self.filename)
        self.assertEqual(data, self.filedata)
