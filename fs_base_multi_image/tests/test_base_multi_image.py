import base64
import io
import os
import tempfile

from odoo_test_helper import FakeModelLoader
from PIL import Image

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestBaseMultiImage(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Disable chatter tracking to avoid dynamic fields
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.env["ir.config_parameter"].set_param(
            "base.image_autoresize_max_px", "10000x10000"
        )

        # Load fake models
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()

        from ..models.fs_image_relation_mixin import (
            FsImageRelationMixin,
        )
        from .models.test_models import FsRelationModelImage, TestModel

        # Register the AbstractModel parent first so FakeModelLoader can resolve the
        # _inherit = "fs.image.relation.mixin" reference in FsRelationModelImage
        cls.loader.update_registry(
            (FsImageRelationMixin, TestModel, FsRelationModelImage)
        )

        # Create test images
        cls.image_w = cls._create_image(4000, 2000)
        cls.image_h = cls._create_image(2000, 4000)

        cls.create_content = cls.image_w
        cls.write_content = cls.image_h

        cls.tmpfile_path = tempfile.mkstemp(suffix=".png")[1]

        with open(cls.tmpfile_path, "wb") as f:
            f.write(cls.create_content)

        cls.filename = os.path.basename(cls.tmpfile_path)

        # Pre-create an fs.image record
        cls.image_white = cls.env["fs.image"].create(
            {
                "image": {
                    "filename": "white.png",
                    "content": base64.b64encode(cls.image_w),
                }
            }
        )

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.tmpfile_path):
            os.remove(cls.tmpfile_path)

        cls.loader.restore_registry()

        super().tearDownClass()

    def check_attrs(self):
        # Deactivate check_attrs to avoid conflict with FakeModelLoader.
        # since superClass uses it for its own puposes not relevant for our tests.
        pass

    @staticmethod
    def _create_image(width, height, color="#4169E1", img_format="PNG"):
        f = io.BytesIO()
        Image.new("RGB", (width, height), color).save(f, img_format)
        f.seek(0)
        return f.read()

    def test_base_relation_image(self):
        instance = self.env["test.model"].create({})

        self.env["fs.relation.model.image"].create(
            {
                "relation_model_id": instance.id,
                "specific_image": {
                    "filename": "white.png",
                    "content": base64.b64encode(self.image_w),
                },
            }
        )

        self.assertEqual(len(instance.image_ids), 1)
        self.assertEqual(instance.image_ids.name, "white.png")
        self.assertEqual(instance.image_ids.mimetype, "image/png")

        self.assertTrue(instance.image_ids.image_medium)

        self.assertEqual(
            instance.image_ids.specific_image_medium,
            instance.image_ids.image_medium,
        )

    def test_base_relation_image_id(self):
        instance = self.env["test.model"].create({})

        self.env["fs.relation.model.image"].create(
            {
                "relation_model_id": instance.id,
                "image_id": self.image_white.id,
            }
        )

        self.assertEqual(instance.image_ids.image_id.name, "white.png")
        self.assertEqual(instance.image_ids.image_id.mimetype, "image/png")
