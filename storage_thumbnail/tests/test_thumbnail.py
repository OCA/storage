import base64
import os

from odoo_test_helper import FakeModelLoader

from odoo.fields import first

from odoo.addons.component.tests.common import SavepointComponentCase


class TestStorageThumbnail(SavepointComponentCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super().tearDownClass()

    def _create_thumbnail(self):
        # create thumbnail
        vals = {"name": "TEST THUMB"}
        self.thumbnail = self.env["storage.thumbnail"].create(vals)

    def _create_model(self, resize=False):
        if resize:
            self.env["ir.config_parameter"].sudo().create(
                {"key": "storage.image.resize.format", "value": ".webp"}
            )
        vals = {"name": self.filename, "image_medium_url": self.filedata}
        self.image = self.env["model.test"].create(vals)

    def test_thumbnail(self):
        self._create_thumbnail()
        self.assertTrue(self.thumbnail.url)
        file_id = self.thumbnail.file_id
        self.assertTrue(file_id)

        self.thumbnail.unlink()
        self.assertTrue(file_id.to_delete)

    def test_model(self):
        self._create_model()
        self.assertTrue(self.image.url)
        self.assertEqual(2, len(self.image.thumbnail_ids))
        self.assertEqual(".png", first(self.image.thumbnail_ids).extension)

    def test_model_resize(self):
        self._create_model(resize=True)
        self.assertIn("webp", first(self.image.thumbnail_ids).url)
        self.assertEqual(".webp", first(self.image.thumbnail_ids).extension)
