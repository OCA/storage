# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import io
import os
import tempfile

from odoo_test_helper import FakeModelLoader
from PIL import Image

from odoo.addons.base.tests.common import BaseCommon
from odoo.addons.fs_image.fields import FSImageValue


class TestBaseMultiImage(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].set_param(
            "base.image_autoresize_max_px", "10000x10000"
        )
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .models import FsRelationModelImage, TestModel

        cls.loader.update_registry((TestModel, FsRelationModelImage))
        cls.image_w = cls._create_image(4000, 2000)
        cls.image_h = cls._create_image(2000, 4000)

        cls.create_content = cls.image_w
        cls.write_content = cls.image_h
        cls.tmpfile_path = tempfile.mkstemp(suffix=".png")[1]
        with open(cls.tmpfile_path, "wb") as f:
            f.write(cls.create_content)
        cls.filename = os.path.basename(cls.tmpfile_path)

        cls.image_white = cls.env["fs.image"].create(
            {
                "image": {
                    "filename": "white.png",
                    "content": base64.b64encode(cls.image_w),
                }
            }
        )

    @classmethod
    def _create_file(cls):
        cls.tmpfile_path = tempfile.mkstemp(suffix=".png")[1]
        with open(cls.tmpfile_path, "wb") as f:
            f.write(cls.create_content)
        cls.filename = os.path.basename(cls.tmpfile_path)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.tmpfile_path):
            os.remove(cls.tmpfile_path)
        cls.loader.restore_registry()
        return super().tearDownClass()

    @classmethod
    def _create_image(cls, width, height, color="#4169E1", img_format="PNG"):
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
        self.assertEqual(1, len(instance.image_ids))
        self.assertEqual("white.png", instance.image_ids.name)
        self.assertEqual("image/png", instance.image_ids.mimetype)

        self.assertTrue(instance.image_ids.image_medium)
        self.assertEqual(
            instance.image_ids.specific_image_medium, instance.image_ids.image_medium
        )

        # Change image and check specific image is set
        new_image = self._create_image(2000, 6000)
        self.create_content = new_image
        self._create_file()
        new_image_value = FSImageValue(name=self.filename, value=self.create_content)
        instance.image_ids.image = new_image_value
        instance.image_ids.invalidate_recordset()
        self.assertEqual(instance.image_ids.image, instance.image_ids.specific_image)

        instance.image_ids.write(
            {
                "specific_image": False,
                "link_existing": True,
                "image": False,
            }
        )
        self.assertTrue(instance.image_ids.specific_image)
        self.assertFalse(instance.image_ids.image)

    def test_base_relation_image_id(self):
        instance = self.env["test.model"].create({})
        self.env["fs.relation.model.image"].create(
            {
                "relation_model_id": instance.id,
                "image_id": self.image_white.id,
            }
        )
        self.assertEqual("white.png", instance.image_ids.image_id.name)
        self.assertFalse(instance.image_ids.image_id.mimetype)
