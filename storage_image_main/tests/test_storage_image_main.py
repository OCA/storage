# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
import base64
import os

from odoo_test_helper import FakeModelLoader

from odoo.addons.component.tests.common import SavepointComponentCase


class TestStorageMainImage(SavepointComponentCase):
    @classmethod
    def get_file_content(cls, image, base_path=None):
        path = base_path or cls.base_path
        with open(os.path.join(path, image), "rb") as f:
            data = f.read()
        return data

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base_path = os.path.dirname(os.path.abspath(__file__))
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()

        # The fake class is imported here !! After the backup_registry
        from .model import ResPartnerImageRelation, ResPartner

        cls.loader.update_registry((ResPartnerImageRelation,))
        cls.loader.update_registry((ResPartner,))

        raw_data = cls.get_file_content("icon.png")
        cls.filesize = len(raw_data)
        cls.filedata = base64.b64encode(raw_data)
        cls.filename = "akretion-logo.png"
        cls.image = cls.env["storage.image"].create(
            {"name": cls.filename, "data": cls.filedata}
        )
        cls.image_2 = cls.env["storage.image"].create(
            {"name": cls.filename, "data": cls.filedata}
        )

        cls.partner = cls.env["res.partner"].create({"name": "A partner with images"})

        cls.env["res.partner.image.relation"].create(
            {"res_partner_id": cls.partner.id, "image_id": cls.image.id, "sequence": 2}
        )

        cls.env["res.partner.image.relation"].create(
            {
                "res_partner_id": cls.partner.id,
                "image_id": cls.image_2.id,
                "sequence": 1,
            }
        )

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super().tearDownClass()

    def test_main_image(self):
        # Check if the main image is the second one (but first by sequence)
        self.assertEqual(self.partner.main_image_id, self.image_2)
