# Copyright 2023 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import io
import os
import shutil
import tempfile

from PIL import Image

from odoo.tests.common import HttpCase


class TestStream(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        temp_dir = tempfile.mkdtemp()
        cls.temp_backend = cls.env["fs.storage"].create(
            {
                "name": "Temp FS Storage",
                "protocol": "file",
                "code": "tmp_dir",
                "directory_path": temp_dir,
                "base_url": "http://my.public.files/",
            }
        )
        cls.temp_dir = temp_dir
        cls.content = b"This is a test attachment"
        cls.attachment_binary = (
            cls.env["ir.attachment"]
            .with_context(
                storage_location=cls.temp_backend.code,
                storage_file_path="test.txt",
            )
            .create({"name": "test.txt", "raw": cls.content})
        )

        cls.image = cls._create_image(128, 128)
        cls.attachment_image = (
            cls.env["ir.attachment"]
            .with_context(
                storage_location=cls.temp_backend.code,
                storage_file_path="test.png",
            )
            .create({"name": "test.png", "raw": cls.image})
        )

        @cls.addClassCleanup
        def cleanup_tempdir():
            shutil.rmtree(temp_dir)

        assert cls.attachment_binary.fs_filename
        assert cls.attachment_image.fs_filename

    def setUp(self):
        super().setUp()
        # enforce temp_backend field since it seems that they are reset on
        # savepoint rollback when managed by server_environment -> TO Be investigated
        self.temp_backend.write(
            {
                "protocol": "file",
                "code": "tmp_dir",
                "directory_path": self.temp_dir,
                "base_url": "http://my.public.files/",
            }
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        for f in os.listdir(cls.temp_dir):
            os.remove(os.path.join(cls.temp_dir, f))

    @classmethod
    def _create_image(cls, width, height, color="#4169E1", img_format="PNG"):
        f = io.BytesIO()
        Image.new("RGB", (width, height), color).save(f, img_format)
        f.seek(0)
        return f.read()

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

    def test_content_url(self):
        self.authenticate("admin", "admin")
        url = f"/web/content/{self.attachment_binary.id}"
        self.assertDownload(
            url,
            headers={},
            assert_status_code=200,
            assert_headers={
                "Content-Type": "text/plain; charset=utf-8",
                "Content-Disposition": "inline; filename=test.txt",
            },
            assert_content=self.content,
        )

    def test_image_url(self):
        self.authenticate("admin", "admin")
        url = f"/web/image/{self.attachment_image.id}"
        self.assertDownload(
            url,
            headers={},
            assert_status_code=200,
            assert_headers={
                "Content-Type": "image/png",
                "Content-Disposition": "inline; filename=test.png",
            },
            assert_content=self.image,
        )

    def test_image_url_with_size(self):
        self.authenticate("admin", "admin")
        url = f"/web/image/{self.attachment_image.id}?width=64&height=64"
        res = self.assertDownload(
            url,
            headers={},
            assert_status_code=200,
            assert_headers={
                "Content-Type": "image/png",
                "Content-Disposition": "inline; filename=test.png",
            },
        )
        self.assertEqual(Image.open(io.BytesIO(res.content)).size, (64, 64))
