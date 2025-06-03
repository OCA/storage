# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import os
import shutil

from odoo import models

from odoo.addons.fs_storage.rooted_dir_file_system import RootedDirFileSystem

from .common import FsFolderTestCase


class TestFsFodlerFieldValueAdapter(FsFolderTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        class FsTestFsFolderFieldValueAdapter(models.AbstractModel):
            _inherit = "fs.folder.field.value.adapter"

            def _created_folder_name_to_stored_value(self, path, storage_code, fs):
                # for the test we inverse the path content
                path = path.lstrip("/")[::-1]
                return super()._created_folder_name_to_stored_value(
                    path, storage_code, fs
                )

            def _get_rooted_dir_file_system(self, value, fs):
                ref = value.ref
                if ref:
                    ref = ref[::-1]
                return RootedDirFileSystem(path=ref, fs=fs)

        cls.loader.update_registry((FsTestFsFolderFieldValueAdapter,))

    def tearDown(self) -> None:
        super().tearDown()
        # empty the temp dir
        for f in os.listdir(self.temp_dir):
            full_path = os.path.join(self.temp_dir, f)
            if os.path.isfile(full_path):
                os.remove(full_path)
            else:
                shutil.rmtree(full_path)

    def test_stored_value(self):
        record = self.fs_test_model.create({"name": "test"})
        self.assertEqual(record.fs_folder, None)
        self.assertFalse(record.fs_folder)
        self.assertEqual(record.fs_folder.fs, None)
        record.fs_folder.initialize()
        #  with our test adapter the ref is the reverse of the name
        self.assertEqual(record.fs_folder.ref, "tset")
        self.assertIsInstance(record.fs_folder.fs, RootedDirFileSystem)
        self.assertEqual(record.fs_folder.stored_value, "tmp_dir://tset")

    def test_rooted_dir_file_system(self):
        record = self.fs_test_model.create({"name": "test"})
        record.fs_folder.initialize()
        self.assertEqual(record.fs_folder.ref, "tset")
        fs = record.fs_folder.fs
        # the rooted dir file system is created with the real path
        self.assertEqual(fs.path, "test")
        self.assertListEqual([], fs.ls(""))
