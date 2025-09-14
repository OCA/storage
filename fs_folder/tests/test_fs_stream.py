# Copyright 2025 ACSONE SA/NV (http://acsone.eu).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import shutil
import tempfile

from odoo.tests.common import HttpCase

from ..fields import FsFolderValue


class TestStream(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        temp_dir = tempfile.mkdtemp()
        cls.temp_backend = cls.env["fs.storage"].create(
            {
                "name": "Temp FS Storage",
                "protocol": "file",
                "code": "tmp_dir",
                "directory_path": temp_dir,
                "use_as_default_for_fs_contents": True,
            }
        )
        cls.temp_dir = temp_dir
        cls.temp_backend.json_options = {"target_options": {"auto_mkdir": "True"}}
        cls.fs = cls.temp_backend._get_filesystem()
        cls.api = cls.env["fs.folder.field.web.api"]
        cls.fs.makedirs("nested")
        cls.fs.pipe_file("nested/test.txt", b"hello")

        # add a field to res.partner
        cls.env["ir.model.fields"].create(
            {
                "name": "x_fs_folder",
                "model_id": cls.env.ref("base.model_res_partner").id,
                "model": "res.partner",
                "ttype": "fs_folder",
            }
        )

        partner = cls.env["res.partner"].create({"name": "test"})
        field = partner._fields["x_fs_folder"]
        partner.x_fs_folder = FsFolderValue(
            f"{cls.temp_backend.code}://nested", field, partner
        )
        cls.record = partner

        @cls.addClassCleanup
        def cleanup_tempdir():
            shutil.rmtree(temp_dir)

    def _get_common_args(self):
        return (self.record.id, self.record._name, "x_fs_folder")

    def setUp(self):
        super().setUp()
        # enforce temp_backend field since it seems that they are reset on
        # savepoint rollback when managed by server_environment -> TO Be investigated
        self.temp_backend.write(
            {
                "protocol": "file",
                "code": "tmp_dir",
                "directory_path": self.temp_dir,
                "use_as_default_for_fs_contents": True,
            }
        )

    def assertDownload(
        self, url, headers, assert_status_code, assert_headers, assert_content=None
    ):
        res = self.url_open(url, headers=headers)
        res.raise_for_status()
        self.assertEqual(res.status_code, assert_status_code)
        for header_name, header_value in assert_headers.items():
            self.assertEqual(
                res.headers.get(header_name),
                header_value,
                f"Wrong value for header {header_name}",
            )
        if assert_content:
            self.assertEqual(res.content, assert_content, "Wong content")
        return res

    def test_preview_url(self):
        self.authenticate("admin", "admin")
        url = self.api.get_url_for_preview(*self._get_common_args(), path="test.txt")
        self.assertDownload(
            url,
            headers={},
            assert_status_code=200,
            assert_headers={
                "Content-Type": "text/plain; charset=utf-8",
                "Content-Disposition": "inline; filename=test.txt",
            },
            assert_content=b"hello",
        )

    def test_download_url(self):
        self.authenticate("admin", "admin")
        url = self.api.get_url_for_download(*self._get_common_args(), path="test.txt")
        self.assertDownload(
            url,
            headers={},
            assert_status_code=200,
            assert_headers={
                "Content-Type": "text/plain; charset=utf-8",
                "Content-Disposition": "attachment; filename=test.txt",
            },
            assert_content=b"hello",
        )
