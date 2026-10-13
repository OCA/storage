# Copyright 2023 ACSONE SA/NV (http://acsone.eu).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import warnings
from unittest import mock

import fsspec

from odoo.exceptions import ValidationError
from odoo.tests import Form
from odoo.tools import config, mute_logger, safe_eval

from ..models import fs_storage as fs_storage_models
from ..rooted_dir_file_system import RootedDirFileSystem
from .common import TestFSStorageCase


class FakeSFTPFileSystem(fsspec.AbstractFileSystem):
    """Filesystem cached by fsspec like SFTP, counting the connections opened"""

    protocol = "fake_sftp"
    opened = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        type(self).opened += 1
        self.ftp = mock.Mock()
        self.client = mock.Mock()

    def info(self, path, **kwargs):
        return {"name": path, "size": 0, "type": "file"}


class TestFSStorage(TestFSStorageCase):
    @mute_logger("py.warnings")
    def _test_deprecated_setting_and_getting_data(self):
        # Check that the directory is empty
        warnings.filterwarnings("ignore")
        files = self.backend.list_files()
        self.assertNotIn(self.filename, files)

        # Add a new file
        self.backend.add(
            self.filename, self.filedata, mimetype="text/plain", binary=False
        )

        # Check that the file exist
        files = self.backend.list_files()
        self.assertIn(self.filename, files)

        # Retrieve the file added
        data = self.backend.get(self.filename, binary=False)
        self.assertEqual(data, self.filedata)

        # Delete the file
        self.backend.delete(self.filename)
        files = self.backend.list_files()
        self.assertNotIn(self.filename, files)

    @mute_logger("py.warnings")
    def _test_deprecated_find_files(self):
        warnings.filterwarnings("ignore")
        self.backend.add(
            self.filename, self.filedata, mimetype="text/plain", binary=False
        )
        try:
            res = self.backend.find_files(r".*\.txt")
            self.assertListEqual([self.filename], res)
            res = self.backend.find_files(r".*\.text")
            self.assertListEqual([], res)
        finally:
            self.backend.delete(self.filename)

    def test_deprecated_setting_and_getting_data_from_root(self):
        self._test_deprecated_setting_and_getting_data()

    def test_deprecated_setting_and_getting_data_from_dir(self):
        self.backend.directory_path = self.case_with_subdirectory
        self._test_deprecated_setting_and_getting_data()

    def test_deprecated_find_files_from_root(self):
        self._test_deprecated_find_files()

    def test_deprecated_find_files_from_dir(self):
        self.backend.directory_path = self.case_with_subdirectory
        self._test_deprecated_find_files()

    def test_ensure_one_fs_by_record(self):
        # in this test we ensure that we've one fs by record
        backend_ids = []
        for i in range(4):
            backend_ids.append(
                self.backend.create(
                    {
                        "name": f"name{i}",
                        "directory_path": f"{i}",
                        "code": f"code{i}",
                        "protocol": "odoofs",
                    }
                ).id
            )
        records = self.backend.browse(backend_ids)
        fs = None
        for rec in records:
            self.assertNotEqual(fs, rec.fs)

    def test_relative_access(self):
        self.backend.directory_path = self.case_with_subdirectory
        self._create_file(self.backend, self.filename, self.filedata)
        other_subdirectory = "other_subdirectory"
        backend2 = self.backend.copy({"directory_path": other_subdirectory})
        self._create_file(backend2, self.filename, self.filedata)
        with self.assertRaises(PermissionError), self.env.cr.savepoint():
            # check that we can't access outside the subdirectory
            backend2.fs.ls("../")
        with self.assertRaises(PermissionError), self.env.cr.savepoint():
            # check that we can't access the file into another subdirectory
            backend2.fs.ls(f"../{self.case_with_subdirectory}")
        self.backend.fs.rm_file(self.filename)
        backend2.fs.rm_file(self.filename)

    def test_recursive_add_odoo_storage_path_to_options(self):
        options = {
            "directory_path": "/tmp/my_backend",
            "target_protocol": "odoofs",
        }
        self.backend._recursive_add_odoo_storage_path(options)
        self.assertEqual(
            self.backend._odoo_storage_path,
            options.get("target_options").get("odoo_storage_path"),
        )
        options = {
            "directory_path": "/tmp/my_backend",
            "target_protocol": "dir",
            "target_options": {
                "path": "/my_backend",
                "target_protocol": "odoofs",
            },
        }
        self.backend._recursive_add_odoo_storage_path(options)
        self.assertEqual(
            self.backend._odoo_storage_path,
            options.get("target_options")
            .get("target_options")
            .get("odoo_storage_path"),
        )

    def test_interface_values(self):
        protocol = "file"  # should be available by default in the list of protocols
        with Form(self.env["fs.storage"]) as new_storage:
            new_storage.name = "Test storage"
            new_storage.code = "code"
            new_storage.protocol = protocol
            self.assertEqual(new_storage.protocol, protocol)
            # the options should follow the protocol
            self.assertEqual(new_storage.options_protocol, protocol)
            description = new_storage.protocol_descr
            self.assertTrue("Interface to files on local storage" in description)
        # this is still true after saving
        self.assertEqual(new_storage.options_protocol, protocol)

    def test_options_env(self):
        self.backend.json_options = {"key": {"sub_key": "$KEY_VAR"}}
        eval_json_options = {"key": {"sub_key": "TEST"}}
        options = self.backend._get_fs_options()
        self.assertDictEqual(options, self.backend.json_options)
        self.backend.eval_options_from_env = True
        with mock.patch.dict("os.environ", {"KEY_VAR": "TEST"}):
            options = self.backend._get_fs_options()
            self.assertDictEqual(options, eval_json_options)
        with self.assertLogs(level="WARNING") as log:
            options = self.backend._get_fs_options()
        self.assertIn(
            (
                f"Environment variable KEY_VAR is not set for "
                f"fs_storage {self.backend.display_name}."
            ),
            log.output[0],
        )

    def test_no_create_in_safe_eval(self):
        # check that we can't create a file in safe_eval
        with self.assertRaisesRegex(
            ValidationError,
            "Calling fs.storage.create is not allowed in a safe_eval context.",
        ):
            safe_eval.safe_eval(
                "env['fs.storage'].create({'name': 'test', 'code': 'test'})",
                {"env": self.env},
            )

        with self.assertRaisesRegex(
            ValidationError,
            "Calling fs.storage.create is not allowed in a safe_eval context.",
        ):
            safe_eval.safe_eval(
                "env['fs.storage']._create({'name': 'test', 'code': 'test'})",
                {"env": self.env},
            )

    def test_no_write_in_safe_eval(self):
        # check that we can't write a file in safe_eval
        with self.assertRaisesRegex(
            ValidationError,
            "Calling fs.storage.write is not allowed in a safe_eval context.",
        ):
            safe_eval.safe_eval(
                "env['fs.storage'].search([]).write({'name': 'test'})",
                {"env": self.env},
            )
        with self.assertRaisesRegex(
            ValidationError,
            "Calling fs.storage.write is not allowed in a safe_eval context.",
        ):
            safe_eval.safe_eval(
                "env['fs.storage'].search([])._write({'name': 'test'})",
                {"env": self.env},
            )

    def test_no_unlink_in_safe_eval(self):
        # check that we can't unlink a file in safe_eval
        with self.assertRaisesRegex(
            ValidationError,
            "Calling fs.storage.unlink is not allowed in a safe_eval context.",
        ):
            safe_eval.safe_eval(
                "env['fs.storage'].search([]).unlink()", {"env": self.env}
            )

    def test_directory_path_substitution(self):
        template = "dir/{db_name}"
        self.backend.directory_path = template
        # Assert different (db name should be replaced)
        self.assertNotEqual(template, self.backend.get_directory_path())

    def test_failed_check_drops_only_its_filesystem(self):
        fs = self.backend.fs
        wrapped_fs = fs.fs
        other_fs = fsspec.filesystem("memory")
        with mock.patch.dict(config.options, {"test_enable": False}), mock.patch.object(
            self.backend.__class__,
            "_check_connection",
            side_effect=OSError("connection lost"),
        ), self.assertRaises(OSError):
            self.backend.fs  # pylint: disable=pointless-statement
        self.assertNotIn(fs._fs_token_, type(fs)._cache)
        # The filesystem wrapped by rooted_dir must not come back from the cache
        self.assertNotIn(wrapped_fs._fs_token_, type(wrapped_fs)._cache)
        # The filesystems of the other storages are kept
        self.assertIn(other_fs._fs_token_, type(other_fs)._cache)

    def _new_sftp_filesystem(self, *args, **kwargs):
        try:
            from fsspec.implementations.sftp import SFTPFileSystem
        except ImportError:
            self.skipTest("paramiko is not installed")
        fs = mock.create_autospec(SFTPFileSystem, instance=True)
        # fsspec gives each filesystem class its own instance cache
        type(fs)._cache = {}
        fs.ftp = mock.Mock()
        fs.client = mock.Mock()
        return fs

    def _sftp_storage(self, code):
        return self.env["fs.storage"].create(
            {
                "name": code,
                "code": code,
                "protocol": "sftp",
                "json_options": {"host": "localhost"},
            }
        )

    def _patch_sftp(self, side_effect):
        for patcher in (
            mock.patch.dict(fs_storage_models._last_filesystems, clear=True),
            mock.patch.object(fsspec, "filesystem", side_effect=side_effect),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_drop_filesystem_closes_sftp_connection(self):
        fs = self._new_sftp_filesystem()
        self.backend._drop_filesystem(fs)
        fs.ftp.close.assert_called_once_with()
        fs.client.close.assert_called_once_with()

    @mute_logger("odoo.addons.fs_storage.models.fs_storage")
    def test_drop_filesystem_closes_client_when_channel_fails(self):
        fs = self._new_sftp_filesystem()
        # paramiko raises when the channel is closed over a broken socket
        fs.ftp.close.side_effect = EOFError()
        self.backend._drop_filesystem(fs)
        fs.client.close.assert_called_once_with()

    def test_replaced_filesystem_closed_when_options_change(self):
        self._patch_sftp(self._new_sftp_filesystem)
        storage = self._sftp_storage("sftp_test")
        fs = storage._get_filesystem()
        storage.json_options = {"host": "localhost", "port": 2222}
        self.assertIsNot(storage._get_filesystem(), fs)
        fs.client.close.assert_called_once_with()

    def test_same_filesystem_not_closed(self):
        fs = self._new_sftp_filesystem()
        self._patch_sftp(lambda *args, **kwargs: fs)
        storage = self._sftp_storage("sftp_test")
        storage._get_filesystem()
        storage._get_filesystem()
        fs.client.close.assert_not_called()

    def test_replaced_filesystem_kept_while_shared(self):
        shared_fs = self._new_sftp_filesystem()
        self._patch_sftp(lambda *args, **kwargs: shared_fs)
        storage = self._sftp_storage("sftp_test")
        other_storage = self._sftp_storage("sftp_other")
        storage._get_filesystem()
        other_storage._get_filesystem()
        fsspec.filesystem.side_effect = self._new_sftp_filesystem
        storage.json_options = {"host": "localhost", "port": 2222}
        storage._get_filesystem()
        # fsspec shares the instance with the other storage, which still uses it
        shared_fs.client.close.assert_not_called()

    def _patch_fake_sftp(self):
        FakeSFTPFileSystem.opened = 0
        self.addCleanup(FakeSFTPFileSystem.clear_instance_cache)
        self._patch_sftp(lambda protocol, **options: FakeSFTPFileSystem(**options))
        patcher = mock.patch.dict(config.options, {"test_enable": False})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_failed_check_reconnects_once(self):
        self._patch_fake_sftp()
        storage = self._sftp_storage("sftp_test")
        with mock.patch.object(
            type(storage), "_check_connection", side_effect=OSError("check KO")
        ), self.assertRaises(OSError):
            storage.fs  # pylint: disable=pointless-statement
        for _i in range(3):
            fs = self.env["fs.storage"].browse(storage.id).fs
        self.assertEqual(FakeSFTPFileSystem.opened, 2)
        fs.client.close.assert_not_called()

    def test_failed_check_keeps_shared_filesystem(self):
        self._patch_fake_sftp()
        storage = self._sftp_storage("sftp_test")
        other_storage = self._sftp_storage("sftp_other")
        shared_fs = other_storage.fs
        with mock.patch.object(
            type(storage), "_check_connection", side_effect=OSError("check KO")
        ), self.assertRaises(OSError):
            storage.fs  # pylint: disable=pointless-statement
        # The other storage still uses the connection
        shared_fs.client.close.assert_not_called()
        self.assertIs(self.env["fs.storage"].browse(other_storage.id).fs, shared_fs)

    def test_failed_check_reconnects_with_directory_path(self):
        self._patch_fake_sftp()
        filesystem = fsspec.filesystem.side_effect

        def rooted_dir_or_sftp(protocol, **options):
            if protocol == "rooted_dir":
                return RootedDirFileSystem(**options)
            return filesystem(protocol, **options)

        fsspec.filesystem.side_effect = rooted_dir_or_sftp
        storage = self._sftp_storage("sftp_test")
        storage.directory_path = "dir"
        broken_fs = storage.fs.fs
        with mock.patch.object(
            type(storage), "_check_connection", side_effect=OSError("check KO")
        ), self.assertRaises(OSError):
            storage.fs  # pylint: disable=pointless-statement
        # The broken connection is closed and the next access gets a new one
        broken_fs.client.close.assert_called_once_with()
        fs = self.env["fs.storage"].browse(storage.id).fs.fs
        self.assertIsNot(fs, broken_fs)
        self.assertEqual(FakeSFTPFileSystem.opened, 2)

    def test_failed_check_on_replaced_filesystem_keeps_current_one(self):
        self._patch_fake_sftp()
        storage = self._sftp_storage("sftp_test")
        old_record = self.env["fs.storage"].browse(storage.id)
        old_fs = old_record.fs
        storage.json_options = {"host": "localhost", "port": 2222}
        current_fs = self.env["fs.storage"].browse(storage.id).fs
        with mock.patch.object(
            type(storage), "_check_connection", side_effect=OSError("check KO")
        ), self.assertRaises(OSError):
            old_record.fs  # pylint: disable=pointless-statement
        # The record holding the replaced filesystem must not forget the current one
        self.assertIsNot(current_fs, old_fs)
        self.assertIs(
            fs_storage_models._last_filesystems[storage._last_filesystem_key()],
            current_fs,
        )
