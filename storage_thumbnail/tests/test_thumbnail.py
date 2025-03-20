import base64
import os

from odoo_test_helper import FakeModelLoader

from odoo.fields import first

from odoo.addons.component.tests.common import TransactionComponentCase


class TestStorageThumbnail(TransactionComponentCase):
    @classmethod
    def setUpClass(cls):
        res = super().setUpClass()
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .models import ModelTest

        cls.loader.update_registry((ModelTest,))
        path = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(path, "static/akretion-logo.png"), "rb") as f:
            data = f.read()
        cls.filesize = len(data)
        cls.filedata = base64.b64encode(data)
        cls.filename = "akretion-logo.png"
        return res

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        return super().tearDownClass()

    def _create_thumbnail(self):
        # create thumbnail
        vals = {"name": "TEST THUMB"}
        return self.env["storage.thumbnail"].create(vals)

    def _create_image(self, resize=False, **kw):
        if resize:
            self.env["ir.config_parameter"].sudo().create(
                {"key": "storage.image.resize.format", "value": ".webp"}
            )
        vals = {"name": self.filename, "data": self.filedata}
        vals.update(kw)
        return self.env["model.test"].create(vals)

    def test_thumbnail(self):
        thumb = self._create_thumbnail()
        self.assertTrue(thumb.url)
        file_id = thumb.file_id
        self.assertTrue(file_id)
        thumb.unlink()
        self.assertTrue(file_id.to_delete)

    def test_image_get_or_create_thumbnail_no_duplicate(self):
        # Ensure no duplicate is generated thanks to unique url_key
        image = self._create_image()
        self.assertTrue(image.url)
        self.assertEqual(len(image.thumbnail_ids), 2)
        thumb = image.thumb_small_id
        thumb.url_key = "test"
        existing_thumb = image.get_or_create_thumbnail(
            thumb.size_x, thumb.size_y, url_key="TEST"
        )
        self.assertEqual(thumb, existing_thumb)

    def test_model(self):
        image = self._create_image()
        self.assertTrue(image.url)
        self.assertEqual(2, len(image.thumbnail_ids))
        self.assertEqual(".png", first(image.thumbnail_ids).extension)

    def test_model_resize(self):
        image = self._create_image(resize=True)
        self.assertIn("webp", first(image.thumbnail_ids).url)
        self.assertEqual(".webp", first(image.thumbnail_ids).extension)

    def test_medium_small(self):
        image = self._create_image()
        self.assertEqual(image.thumb_medium_id.size_x, 128)
        self.assertEqual(image.thumb_medium_id.size_y, 128)
        self.assertEqual(image.thumb_small_id.size_x, 64)
        self.assertEqual(image.thumb_small_id.size_y, 64)

    def test_urls(self):
        image1 = self._create_image()
        image2 = self._create_image(name="another.png")
        images = image1 + image2
        # Make it server externally
        self.assertFalse(image1.backend_id.backend_view_use_internal_url)
        image1.backend_id.served_by = "external"
        cdn = "https://somewhere.com"
        image1.backend_id.base_url = cdn

        t1_med_file = image1.thumb_medium_id.file_id
        t1_small_file = image1.thumb_small_id.file_id
        t2_med_file = image2.thumb_medium_id.file_id
        t2_small_file = image2.thumb_small_id.file_id

        # Internal URL use CDN by default
        expected = [
            {
                "url": f"{cdn}/akretion-logo-{image1.file_id.id}.png",
                "internal_url": f"/storage.file/akretion-logo-{image1.file_id.id}.png",
                "image_medium_url": f"{cdn}/akretion-logo_128_128-{t1_med_file.id}.png",
                "image_small_url": f"{cdn}/akretion-logo_64_64-{t1_small_file.id}.png",
            },
            {
                "url": f"{cdn}/another-{image2.file_id.id}.png",
                "internal_url": f"/storage.file/another-{image2.file_id.id}.png",
                "image_medium_url": f"{cdn}/another_128_128-{t2_med_file.id}.png",
                "image_small_url": f"{cdn}/another_64_64-{t2_small_file.id}.png",
            },
        ]
        self.assertRecordValues(images, expected)
        # Unless we enforce it
        image1.backend_id.backend_view_use_internal_url = True
        images.invalidate_recordset()
        expected = [
            {
                "url": f"{cdn}/akretion-logo-{image1.file_id.id}.png",
                "internal_url": f"/storage.file/akretion-logo-{image1.file_id.id}.png",
                "image_medium_url": (
                    f"/storage.file/akretion-logo_128_128-{t1_med_file.id}.png"
                ),
                "image_small_url": (
                    f"/storage.file/akretion-logo_64_64-{t1_small_file.id}.png"
                ),
            },
            {
                "url": f"{cdn}/another-{image2.file_id.id}.png",
                "internal_url": f"/storage.file/another-{image2.file_id.id}.png",
                "image_medium_url": (
                    f"/storage.file/another_128_128-{t2_med_file.id}.png"
                ),
                "image_small_url": (
                    f"/storage.file/another_64_64-{t2_small_file.id}.png"
                ),
            },
        ]
        self.assertRecordValues(images, expected)
