# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import os
import urllib
from unittest.mock import patch

from odoo_test_helper import FakeModelLoader

from odoo.addons.component.tests.common import SavepointComponentCase


class TestImportImage(SavepointComponentCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def _import_image(self, vals):
        path = os.path.dirname(os.path.abspath(__file__))
        image = open(os.path.join(path, "static/oca-logo.png"), "rb")

        with patch.object(urllib.request, "urlopen", return_value=image):
            self.env["image.relation.abstract"]._process_import_from_url(vals)

    def test_create(self):
        vals = {
            "import_from_url": ("https://www.exemple.com/product_images/oca-logo.png")
        }
        self._import_image(vals)
        self.assertIn("image_id", vals)
        self.env["storage.image"].browse(vals["image_id"]).data

    def test_reimport(self):
        vals = {
            "import_from_url": ("https://www.exemple.com/product_images/oca-logo.png")
        }
        self._import_image(vals)
        image_id = vals["image_id"]
        vals = {
            "import_from_url": ("https://www.exemple.com/product_images/oca-logo.png")
        }
        self._import_image(vals)
        self.assertEqual(image_id, vals["image_id"])


class ImportImageCase(SavepointComponentCase):
    @classmethod
    def setUpClass(cls):
        super(ImportImageCase, cls).setUpClass()
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()

        # The fake class is imported here !! After the backup_registry
        from .models import FakeProductImageRelation

        cls.oca_image = cls._create_storage_image("akretion-logo.png")
        cls.akretion_image = cls._create_storage_image("oca-logo.png")

        cls.loader.update_registry((FakeProductImageRelation,))

    @staticmethod
    def _get_file_content(name, base_path=None, as_binary=False):
        path = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(path, "static/", name), "rb") as f:
            data = f.read()
        if as_binary:
            return data
        return base64.b64encode(data)

    @classmethod
    def _create_storage_image(cls, name):
        return cls.env["storage.image"].create(
            {"name": name, "data": cls._get_file_content(name)}
        )

    def _create_multi_image(self, vals_list):
        for vals in vals_list:
            path = os.path.dirname(os.path.abspath(__file__))
            if vals["image_id"] == self.oca_image.id:
                image = open(os.path.join(path, "static/oca-logo.png"), "rb")
            elif vals["image_id"] == self.akretion_image.id:
                image = open(os.path.join(path, "static/akretion-logo.png"), "rb")
            with patch.object(urllib.request, "urlopen", return_value=image):
                self.env["product.image.relation"].create(vals_list)

    def _id_present(self, img):
        id_present = self.env["storage.image"].search([("id", "=", img.id)])
        return id_present

    def test_create_multi(self):
        self.env["product.image.relation"].create(
            [{"image_id": self.oca_image.id}, {"image_id": self.akretion_image.id}]
        )

        id_present = self._id_present(self.oca_image)
        id2_present = self._id_present(self.akretion_image)
        self.assertTrue(id_present.name, "oca-logo.png")
        self.assertTrue(id2_present.name, "akretion-logo.png")
        self.assertTrue(id_present.data)
        self.assertTrue(id2_present.data)

    def test_create_multi_with_import_from_url(self):
        vals_list = [
            {
                "image_id": self.oca_image.id,
                "import_from_url": (
                    "https://www.exemple.com/product_images/oca-logo.png"
                ),
            },
            {
                "image_id": self.akretion_image.id,
                "import_from_url": (
                    "https://www.exemple.com/product_images/akretion-logo.png"
                ),
            },
        ]

        self._create_multi_image(vals_list)

        id_present = self._id_present(self.oca_image)
        id2_present = self._id_present(self.akretion_image)
        self.assertTrue(id_present.name, "oca-logo.png")
        self.assertTrue(id2_present.name, "akretion-logo.png")
        self.assertTrue(id_present.data)
        self.assertTrue(id2_present.data)
