# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import os
import urllib
from unittest.mock import patch

from odoo.addons.component.tests.common import SavepointComponentCase

# from ..models.image_relation_abstract import ImageRelationAbstract


class TestImportImage(SavepointComponentCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def _import_image(self, vals):
        path = os.path.dirname(os.path.abspath(__file__))
        image = open(os.path.join(path, "static/test.png"), "rb")

        with patch.object(urllib.request, "urlopen", return_value=image):
            self.env["image.relation.abstract"]._process_import_from_url(vals)

    def test_create(self):
        vals = {"import_from_url": ("https://www.exemple.com/product_images/test.png")}
        self._import_image(vals)
        self.assertIn("image_id", vals)
        self.env["storage.image"].browse(vals["image_id"]).data

    def test_reimport(self):
        vals = {"import_from_url": ("https://www.exemple.com/product_images/test.png")}
        self._import_image(vals)
        image_id = vals["image_id"]
        vals = {"import_from_url": ("https://www.exemple.com/product_images/test.png")}
        self._import_image(vals)
        self.assertEqual(image_id, vals["image_id"])
