# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# Copyright 2019 Camptocamp (http://www.camptocamp.com).
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# pylint: disable=missing-manifest-dependency
# disable warning on 'vcr' missing in manifest: this is only a dependency for
# dev/tests

import errno
import logging
import os

import mock

from odoo.addons.storage_backend.tests.common import Common, GenericStoreCase

_logger = logging.getLogger(__name__)

MOD_PATH = "odoo.addons.storage_backend_sftp.components.sftp_adapter"
PARAMIKO_PATH = MOD_PATH + ".paramiko"


class SftpCase(Common, GenericStoreCase):
    def setUp(self):
        super(SftpCase, self).setUp()
        self.backend.write(
            {
                "backend_type": "sftp",
                "sftp_login": "foo",
                "sftp_password": "pass",
                "sftp_server": os.environ.get("SFTP_HOST", "localhost"),
                "sftp_port": os.environ.get("SFTP_PORT", "2222"),
                "directory_path": "upload",
            }
        )
        self.case_with_subdirectory = "upload/subdirectory/here"

    @mock.patch(MOD_PATH + ".sftp_mkdirs")
    @mock.patch(PARAMIKO_PATH)
    def test_add(self, mocked_paramiko, mocked_mkdirs):
        client = mocked_paramiko.SFTPClient.from_transport()
        # simulate errors
        exc = IOError()
        # general
        client.stat.side_effect = exc
        with self.assertRaises(IOError):
            self.backend._add_bin_data("fake/path", b"fake data")
        # not found
        exc.errno = errno.ENOENT
        client.stat.side_effect = exc
        fakefile = open("/tmp/fakefile.txt", "w+b")
        client.open.return_value = fakefile
        self.backend._add_bin_data("fake/path", b"fake data")
        # mkdirs has been called
        mocked_mkdirs.assert_called()
        # file has been written and closed
        self.assertTrue(fakefile.closed)
        with open("/tmp/fakefile.txt", "r") as thefile:
            self.assertEqual(thefile.read(), "fake data")

    @mock.patch(PARAMIKO_PATH)
    def test_get(self, mocked_paramiko):
        client = mocked_paramiko.SFTPClient.from_transport()
        with open("/tmp/fakefile2.txt", "w+b") as fakefile:
            fakefile.write(b"filecontent")
        client.open.return_value = open("/tmp/fakefile2.txt", "r")
        self.assertEqual(
            self.backend._get_bin_data("fake/path"), "filecontent"
        )

    @mock.patch(PARAMIKO_PATH)
    def test_list(self, mocked_paramiko):
        client = mocked_paramiko.SFTPClient.from_transport()
        # simulate errors
        exc = IOError()
        # general
        client.listdir.side_effect = exc
        with self.assertRaises(IOError):
            self.backend._list()
        # not found
        exc.errno = errno.ENOENT
        client.listdir.side_effect = exc
        self.assertEqual(self.backend._list(), [])

    def test_setting_and_getting_data_from_root(self):
        # bypass as we tested all the methods mocked specifically above.
        # Would be nice to have an integration test but is not feasible ATM.
        pass

    def test_setting_and_getting_data_from_dir(self):
        # bypass as we tested all the methods mocked specifically above
        # Would be nice to have an integration test but is not feasible ATM.
        pass
