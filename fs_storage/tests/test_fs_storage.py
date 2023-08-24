# Copyright 2023 ACSONE SA/NV (http://acsone.eu).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import base64
import shutil
import tempfile
import warnings
from unittest import mock

from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger

from ..models.fs_storage import FSStorage


class TestFSStorage(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.backend: FSStorage = cls.env.ref("fs_storage.default_fs_storage")
        cls.backend.json_options = {"target_options": {"auto_mkdir": "True"}}
        cls.filedata = base64.b64encode(b"This is a simple file")
        cls.filename = "test_file.txt"
        cls.case_with_subdirectory = "subdirectory/here"
        cls.demo_user = cls.env.ref("base.user_demo")

    def setUp(self):
        super().setUp()
        mocked_backend = mock.patch.object(
            self.backend.__class__, "_get_filesystem_storage_path"
        )
        mocked_get_filesystem_storage_path = mocked_backend.start()
        tempdir = tempfile.mkdtemp()
        mocked_get_filesystem_storage_path.return_value = tempdir

        # pylint: disable=unused-variable
        @self.addCleanup
        def stop_mock():
            mocked_backend.stop()
            # recursively delete the tempdir
            shutil.rmtree(tempdir)

    def _create_file(self, backend: FSStorage, filename: str, filedata: str):
        with backend.fs.open(filename, "wb") as f:
            f.write(filedata)

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
                    {"name": f"name{i}", "directory_path": f"{i}", "code": f"code{i}"}
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
