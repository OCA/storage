# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import os
import shutil
from unittest import mock

from odoo.addons.fs_storage.rooted_dir_file_system import RootedDirFileSystem

from .common import FsFolderTestCase


class TestFields(FsFolderTestCase):
    def tearDown(self) -> None:
        super().tearDown()
        # empty the temp dir
        for f in os.listdir(self.temp_dir):
            full_path = os.path.join(self.temp_dir, f)
            if os.path.isfile(full_path):
                os.remove(full_path)
            else:
                shutil.rmtree(full_path)

    def test_create_default(self):
        record = self.fs_test_model.create({"name": "test"})
        self.assertEqual(record.fs_folder, None)
        self.assertFalse(record.fs_folder)
        self.assertEqual(record.fs_folder.fs, None)
        record.fs_folder.initialize()
        self.assertEqual(record.fs_folder.ref, record.name)
        self.assertIsInstance(record.fs_folder.fs, RootedDirFileSystem)
        self.assertEqual(record.fs_folder.stored_value, f"tmp_dir://{record.name}")

    def test_create_hooks(self):
        record = self.fs_test_model.create({"name": "test"})
        with mock.patch.object(self.temp_backend.fs.__class__, "mkdir") as mocked_mkdir:
            record.fs_folder1.initialize()
            mocked_mkdir.assert_called_once_with(
                "custom_parent/custom_name", key="value"
            )

    def test_delegate_fs_folder(self):
        # On a model with FsFolder inherited by delegation:
        # Test that the methods specified on the inherited field to get the
        # parent, the name and the properties to use to create a folder
        # are property called.
        record = self.fs_test_model_inherits.create({"name": "folder_name"})
        with mock.patch.object(self.temp_backend.fs.__class__, "mkdir") as mocked_mkdir:
            record.fs_folder1.initialize()
            mocked_mkdir.assert_called_once_with(
                "custom_parent/custom_name", key="value"
            )

        # check that the value is on the parent and the child instances.
        record.fs_folder2.initialize()
        self.assertEqual(record.fs_folder2.ref, "_create_method")
        self.assertEqual(record.fs_test_model_id.fs_folder2.ref, "_create_method")
        record = self.fs_test_model.create({"name": "test"})
        record.fs_folder1.initialize()
        record2 = self.fs_test_model_related.create(
            {"name": "test", "fs_test_model_id": record.id}
        )
        self.assertEqual(
            record2.fs_folder1.stored_value, record.fs_folder1.stored_value
        )

    def test_related_fs_folder(self):
        # On a model with related FsFolder:
        # Test that the methods specified on the inherited field to get the
        # parent, the name and the properties to use to create a folder
        # are property called.
        parent = self.fs_test_model.create({"name": "folder_parent"})
        record = self.fs_test_model_related.create(
            {"name": "folder_name", "fs_test_model_id": parent.id}
        )
        with mock.patch.object(self.temp_backend.fs.__class__, "mkdir") as mocked_mkdir:
            record.fs_folder1.initialize()
            mocked_mkdir.assert_called_once_with(
                "custom_parent/custom_name", key="value"
            )

        # check that the value is on the parent and the child instances.
        record.fs_folder2.initialize()
        self.assertEqual(record.fs_folder2.ref, "_create_method")
        self.assertEqual(record.fs_test_model_id.fs_folder2.ref, "_create_method")
        self.assertEqual(record.fs_folder2, record.fs_test_model_id.fs_folder2)

    def test_fs_folder_create_multi(self):
        # the create method can be called on a recordset
        inst1 = self.fs_test_model.create({"name": "folder_name1"})
        inst2 = self.fs_test_model.create({"name": "folder_name2"})
        inst1._fields["fs_folder"].create_value(inst1 + inst2)
        self.assertEqual(inst1.fs_folder.ref, "folder_name1")
        self.assertEqual(inst2.fs_folder.ref, "folder_name2")

    def test_fs_folder_copy_false(self):
        # By default FsFolder fields are not copied
        record = self.fs_test_model.create({"name": "folder_name1"})
        record.fs_folder.initialize()
        record_copy = record.copy()
        self.assertEqual(record_copy.fs_folder, None)

    def test_fs_folder_read(self):
        record = self.fs_test_model.create({"name": "folder_name1"})
        record.fs_folder.initialize()
        values = self.fs_test_model.browse(record.id).read(["fs_folder"])[0]
        self.assertDictEqual(
            values["fs_folder"],
            {
                "ref": "folder_name1",
                "storage_code": "tmp_dir",
                "protocol": ("file", "local"),
            },
        )
        record = self.fs_test_model.create({"name": "folder_name2"})
        values = self.fs_test_model.browse(record.id).read(["fs_folder"])[0]
        self.assertFalse(values["fs_folder"])

    def test_fs_folder_name_sanitiez(self):
        record = self.fs_test_model.create({"name": "folder/name"})
        with mock.patch.object(record.__class__, "_get_parent") as mocked_get_parent:
            mocked_get_parent.return_value = dict.fromkeys(
                record.ids, ["*parent*", "ti/ti"]
            )
            record.fs_folder1.initialize()
            self.assertEqual(record.fs_folder1.ref, "_parent_/ti_ti/custom_name")
        record.fs_folder.initialize()
        self.assertEqual(record.fs_folder.ref, "folder_name")
