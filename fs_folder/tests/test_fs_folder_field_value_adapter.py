# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import os
import shutil

from odoo.addons.fs_storage.rooted_dir_file_system import RootedDirFileSystem

from .common import FsFolderTestCase


class TestFsFodlerFieldValueAdapter(FsFolderTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # We can't use add_to_registry here because the model has no _name of
        # its own (_inherit), so instead we patch the method directly and restore it
        # after the test.
        adapter_cls = cls.registry["fs.folder.field.value.adapter"]
        original_created = adapter_cls._created_folder_name_to_stored_value
        original_rooted = adapter_cls._get_rooted_dir_file_system

        def reversed_created(self, path, storage_code, fs):
            path = path.lstrip("/")[::-1]
            return original_created(self, path, storage_code, fs)

        def reversed_rooted(self, value, fs):
            ref = value.ref
            if ref:
                ref = ref[::-1]
            return RootedDirFileSystem(path=ref, fs=fs)

        adapter_cls._created_folder_name_to_stored_value = reversed_created
        adapter_cls._get_rooted_dir_file_system = reversed_rooted
        cls.addClassCleanup(
            setattr,
            adapter_cls,
            "_created_folder_name_to_stored_value",
            original_created,
        )
        cls.addClassCleanup(
            setattr, adapter_cls, "_get_rooted_dir_file_system", original_rooted
        )

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
