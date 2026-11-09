# Copyright 2023 ACSONE SA/NV (http://acsone.eu).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import warnings
from contextlib import contextmanager
from unittest import mock

import fsspec

from odoo.exceptions import ValidationError
from odoo.tests import Form
from odoo.tools import config, mute_logger, safe_eval

from .common import TestFSStorageCase


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

    @contextmanager
    def _server_connection_check(self, side_effect):
        """Run the connection check of ``fs`` as on a running server."""
        with mock.patch.object(
            type(self.backend), "_check_connection", side_effect=side_effect
        ) as check, mock.patch.dict(config.options, {"test_enable": False}):
            yield check

    def test_fs_reconnects_when_check_fails(self):
        # A new record object: the filesystem is kept on the record object.
        backend = self.backend.browse(self.backend.id)
        connection = backend._get_filesystem().fs
        with self._server_connection_check(
            [OSError("Connection lost"), True]
        ) as check, mute_logger("odoo.addons.fs_storage.models.fs_storage"):
            fs = backend.fs
        self.assertEqual(check.call_count, 2)
        self.assertIsNot(fs.fs, connection)

    def test_fs_raises_when_reconnect_fails(self):
        backend = self.backend.browse(self.backend.id)
        with self._server_connection_check(
            OSError("Connection lost")
        ) as check, mute_logger("odoo.addons.fs_storage.models.fs_storage"):
            with self.assertRaises(OSError):
                backend.fs  # pylint: disable=pointless-statement
        self.assertEqual(check.call_count, 2)

    def test_fs_does_not_reconnect_on_refusal(self):
        backend = self.backend.browse(self.backend.id)
        connection = backend._get_filesystem().fs
        with self._server_connection_check(
            PermissionError("Read-only directory")
        ) as check:
            with self.assertRaises(PermissionError):
                backend.fs  # pylint: disable=pointless-statement
        self.assertEqual(check.call_count, 1)
        self.assertIs(backend._get_filesystem().fs, connection)

    def test_clear_filesystem_cache(self):
        wrapper = fsspec.filesystem("simplecache", target_protocol="memory")
        connection = wrapper.fs
        other_connection = fsspec.filesystem("memory", other=True)
        self.backend._clear_filesystem_cache(wrapper)
        new_wrapper = fsspec.filesystem("simplecache", target_protocol="memory")
        self.assertIsNot(new_wrapper, wrapper)
        self.assertIsNot(new_wrapper.fs, connection)
        self.assertIs(fsspec.filesystem("memory", other=True), other_connection)
