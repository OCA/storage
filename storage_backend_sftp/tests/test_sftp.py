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

from odoo.addons.storage_backend.tests.common import BackendStorageTestMixin, CommonCase

_logger = logging.getLogger(__name__)

MOD_PATH = "odoo.addons.storage_backend_sftp.components.sftp_adapter"
ADAPTER_PATH = MOD_PATH + ".SFTPStorageBackendAdapter"
PARAMIKO_PATH = MOD_PATH + ".paramiko"


class SftpCase(CommonCase, BackendStorageTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend.write(
            {
                "backend_type": "sftp",
                "sftp_login": "foo",
                "sftp_password": "pass",
                "sftp_server": os.environ.get("SFTP_HOST", "localhost"),
                "sftp_port": os.environ.get("SFTP_PORT", "2222"),
                "directory_path": "upload",
            }
        )
        cls.case_with_subdirectory = "upload/subdirectory/here"

    @mock.patch(MOD_PATH + ".sftp_mkdirs")
    @mock.patch(PARAMIKO_PATH)
    def test_add(self, mocked_paramiko, mocked_mkdirs):
        client = mocked_paramiko.SFTPClient.from_transport()
        # simulate errors
        exc = IOError()
        # general
        client.stat.side_effect = exc
        with self.assertRaises(IOError):
            self.backend.add("fake/path", b"fake data")
        # not found
        exc.errno = errno.ENOENT
        client.stat.side_effect = exc
        fakefile = open("/tmp/fakefile.txt", "w+b")
        client.open.return_value = fakefile
        self.backend.add("fake/path", b"fake data")
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
        self.assertEqual(self.backend.get("fake/path"), "filecontent")

    @mock.patch(PARAMIKO_PATH)
    def test_list(self, mocked_paramiko):
        client = mocked_paramiko.SFTPClient.from_transport()
        # simulate errors
        exc = IOError()
        # general
        client.listdir.side_effect = exc
        with self.assertRaises(IOError):
            self.backend.list_files()
        # not found
        exc.errno = errno.ENOENT
        client.listdir.side_effect = exc
        self.assertEqual(self.backend.list_files(), [])

    def test_find_files(self):
        good_filepaths = ["somepath/file%d.good" % x for x in range(1, 10)]
        bad_filepaths = ["somepath/file%d.bad" % x for x in range(1, 10)]
        mocked_filepaths = bad_filepaths + good_filepaths
        backend = self.backend.sudo()
        expected = good_filepaths[:]
        expected = [backend.directory_path + "/" + path for path in good_filepaths]
        self._test_find_files(
            backend, ADAPTER_PATH, mocked_filepaths, r".*\.good$", expected
        )

    @mock.patch(PARAMIKO_PATH)
    def test_move_files(self, mocked_paramiko):
        client = mocked_paramiko.SFTPClient.from_transport()
        # simulate file is not already there
        client.lstat.side_effect = FileNotFoundError()
        to_move = "move/from/path/myfile.txt"
        to_path = "move/to/path"
        self.backend.move_files([to_move], to_path)
        # no need to delete it
        client.unlink.assert_not_called()
        # rename gets called
        client.rename.assert_called_with(to_move, to_move.replace("from", "to"))
        # now try to override destination
        client.lstat.side_effect = None
        client.lstat.return_value = True
        self.backend.move_files([to_move], to_path)
        # client will delete it first
        client.unlink.assert_called_with(to_move.replace("from", "to"))
        # then move it
        client.rename.assert_called_with(to_move, to_move.replace("from", "to"))
