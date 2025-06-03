# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import base64
import os

from odoo.tools import mute_logger

from ..fields import FsFolderValue
from .common import FsFolderTestCase

TEXT_FILES = {
    "nested/file1": b"hello\n",
    "nested/file2": b"world",
    "nested/nested2/file1": b"hello\n",
    "nested/nested2/file2": b"world",
}


class TestFsFolderFieldWebApi(FsFolderTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.temp_backend.json_options = {"target_options": {"auto_mkdir": "True"}}
        fs = cls.temp_backend._get_filesystem()
        for flist in [
            TEXT_FILES,
        ]:
            for path, data in flist.items():
                root, _filename = os.path.split(path)
                if root:
                    fs.makedirs(root, exist_ok=True)
                with fs.open(path, "wb") as f:
                    f.write(data)
        fs.copy("nested", "initial_value", recursive=True)
        cls.fs = fs
        cls.record = cls.fs_test_model.create({"name": "nested_content"})
        field = cls.record._fields["fs_folder"]
        cls.record.fs_folder = FsFolderValue(
            f"{cls.temp_backend.code}://nested", field, cls.record
        )
        cls.record.flush_recordset()
        cls.api = cls.env["fs.folder.field.web.api"]

    def _get_common_args(self, field_name="fs_folder"):
        return (self.record.id, self.record._name, field_name)

    def tearDown(self):
        self.fs.rm("nested", recursive=True)
        self.fs.copy("initial_value", "nested", recursive=True)
        super().tearDown()

    def _filter_info(self, data, *keys):
        return {k: data[k] for k in keys}

    def _filter_info_list(self, data, *keys, sort_key="name"):
        data = sorted(data, key=lambda x: x[sort_key])
        return [self._filter_info(item, *keys) for item in data]

    @mute_logger("odoo.addons.fs_folder.models.fs_folder_field_web_api")
    def test_wrong_field(self):
        # case where the field name is unknown
        with self.assertRaises(ValueError):
            self.api._get_fs(self.record.id, self.record._name, field_name="wrong")

        # case where the field is not a fs_folder field
        with self.assertRaises(ValueError):
            self.api._get_fs(self.record.id, self.record._name, field_name="name")

        # case where the  model is unknown
        with self.assertRaises(ValueError):
            self.api._get_fs(self.record.id, "wrong", field_name="fs_folder")

    def test_initilize(self):
        self.assertFalse(self.record.fs_folder1)
        self.api.initialize_field_value(*self._get_common_args("fs_folder1"))
        self.assertTrue(self.record.fs_folder1)

    def test_get_root(self):
        root_info = self.api.get_root(*self._get_common_args())
        self.assertEqual(
            root_info["name"],
            "",
            "Root name should be empty and not refer to the real folder path",
        )
        self.assertEqual(root_info["type"], "directory")

    def test_get_children(self):
        children = self.api.get_children(*self._get_common_args(), path="")
        children = self._filter_info_list(children, "name", "type")
        self.assertEqual(
            children,
            [
                {"name": "file1", "type": "file"},
                {"name": "file2", "type": "file"},
                {"name": "nested2", "type": "directory"},
            ],
        )

        children = self.api.get_children(*self._get_common_args(), path="nested2")
        children = self._filter_info_list(children, "name", "type")
        self.assertEqual(
            children,
            [
                {"name": "nested2/file1", "type": "file"},
                {"name": "nested2/file2", "type": "file"},
            ],
        )

    def test_rename_file(self):
        self.api.rename(
            *self._get_common_args(), "nested2/file2", "nested2/file2_renamed"
        )
        children = self.api.get_children(*self._get_common_args(), path="nested2")
        children = self._filter_info_list(children, "name")
        self.assertEqual(
            children,
            [{"name": "nested2/file1"}, {"name": "nested2/file2_renamed"}],
        )

    def test_rename_folder(self):
        self.api.rename(*self._get_common_args(), "nested2", "nested3")
        children = self.api.get_children(*self._get_common_args(), path="")
        children = self._filter_info_list(children, "name")
        self.assertEqual(
            children, [{"name": "file1"}, {"name": "file2"}, {"name": "nested3"}]
        )

    def test_create_folder(self):
        self.api.create_folder(*self._get_common_args(), path="nested3")
        children = self.api.get_children(*self._get_common_args(), path="")
        children = self._filter_info_list(children, "name")
        self.assertEqual(
            children,
            [
                {"name": "file1"},
                {"name": "file2"},
                {"name": "nested2"},
                {"name": "nested3"},
            ],
        )
        self.api.create_folder(*self._get_common_args(), path="nested3/nested/nested")
        children = self.api.get_children(*self._get_common_args(), path="nested3")
        children = self._filter_info_list(children, "name")
        self.assertEqual(children, [{"name": "nested3/nested"}])
        children = self.api.get_children(
            *self._get_common_args(), path="nested3/nested"
        )
        children = self._filter_info_list(children, "name")
        self.assertEqual(children, [{"name": "nested3/nested/nested"}])

    def test_move_file(self):
        self.api.rename(*self._get_common_args(), "nested2/file2", "file3")
        children = self.api.get_children(*self._get_common_args(), path="")
        children = self._filter_info_list(children, "name")
        self.assertEqual(
            children,
            [
                {"name": "file1"},
                {"name": "file2"},
                {"name": "file3"},
                {"name": "nested2"},
            ],
        )

    def test_upload_file(self):
        self.api.upload_file(
            *self._get_common_args(),
            path="nested2",
            file_name="test.txt",
            file_data=base64.b64encode(b"hello"),
        )
        children = self.api.get_children(*self._get_common_args(), path="nested2")
        children = self._filter_info_list(children, "name")
        self.assertEqual(
            children,
            [
                {"name": "nested2/file1"},
                {"name": "nested2/file2"},
                {"name": "nested2/test.txt"},
            ],
        )
        fs = self.record.fs_folder.fs
        content = fs.open("nested2/test.txt", "rb").read()
        self.assertEqual(content, b"hello")

    def test_update_content(self):
        initial_content = self.fs.open("nested/file1", "rb").read()
        new_content = initial_content + b"\nnew content"
        self.api.update_content(
            *self._get_common_args(),
            path="file1",
            file_data=base64.b64encode(new_content),
        )
        fs = self.record.fs_folder.fs
        content = fs.open("file1", "rb").read()
        self.assertEqual(content, new_content)

    def test_copy_file(self):
        self.api.copy_item(
            *self._get_common_args(), path="file1", new_path="file1_copy"
        )
        children = self.api.get_children(*self._get_common_args(), path="")
        children = self._filter_info_list(children, "name")
        self.assertEqual(
            children,
            [
                {"name": "file1"},
                {"name": "file1_copy"},
                {"name": "file2"},
                {"name": "nested2"},
            ],
        )

    def test_copy_folder(self):
        self.api.copy_item(
            *self._get_common_args(),
            path="nested2",
            new_path="nested2_copy",
            recursive=True,
        )
        children = self.api.get_children(*self._get_common_args(), path="")
        children = self._filter_info_list(children, "name")
        self.assertEqual(
            children,
            [
                {"name": "file1"},
                {"name": "file2"},
                {"name": "nested2"},
                {"name": "nested2_copy"},
            ],
        )
        children = self.api.get_children(*self._get_common_args(), path="nested2_copy")
        children = self._filter_info_list(children, "name")
        self.assertEqual(
            children,
            [
                {"name": "nested2_copy/file1"},
                {"name": "nested2_copy/file2"},
            ],
        )

    def test_delete_file(self):
        self.api.delete(*self._get_common_args(), path="file1")
        children = self.api.get_children(*self._get_common_args(), path="")
        children = self._filter_info_list(children, "name")
        self.assertEqual(children, [{"name": "file2"}, {"name": "nested2"}])

    def test_delete_folder(self):
        self.api.delete(*self._get_common_args(), path="nested2", recursive=True)
        children = self.api.get_children(*self._get_common_args(), path="")
        children = self._filter_info_list(children, "name")
        self.assertEqual(children, [{"name": "file1"}, {"name": "file2"}])
