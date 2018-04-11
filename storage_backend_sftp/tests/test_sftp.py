# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# pylint: disable=missing-manifest-dependency
# disable warning on 'vcr' missing in manifest: this is only a dependency for
# dev/tests

from odoo.addons.storage_backend.tests.common import Common, GenericStoreCase
import os
import logging
_logger = logging.getLogger(__name__)


class SftpCase(Common, GenericStoreCase):

    def setUp(self):
        super(SftpCase, self).setUp()
        self.backend.write({
            'backend_type': 'sftp',
            'sftp_login': 'foo',
            'sftp_password': 'pass',
            'sftp_server': os.environ.get('SFTP_HOST', 'localhost'),
            'sftp_port': os.environ.get('SFTP_PORT', '2222'),
            'directory_path': 'upload',
            })
        self.case_with_subdirectory = 'upload/subdirectory/here'
