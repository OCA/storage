# Copyright 2023 ACSONE SA/NV (http://acsone.eu).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import base64
import warnings

from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestStorageBackend(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.backend = cls.env.ref("storage_backend.default_storage_backend")
        cls.filedata = base64.b64encode(b"This is a simple file")
        cls.filename = "test_file.txt"
        cls.case_with_subdirectory = "subdirectory/here"
        cls.demo_user = cls.env.ref("base.user_demo")

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
                self.backend.create({"name": f"name{i}", "directory_path": f"{i}"}).id
            )
        records = self.backend.browse(backend_ids)
        fs = None
        for rec in records:
            self.assertNotEqual(fs, rec.fs)
