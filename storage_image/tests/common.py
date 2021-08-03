# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# Copyright 2021 Camptocamp (http://www.camptocamp.com).
# @author Iván Todorovich <ivan.todorovich@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import os

from odoo.addons.component.tests.common import SavepointComponentCase


class StorageImageCommonCase(SavepointComponentCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base_path = os.path.dirname(os.path.abspath(__file__))
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        # Run tests with demo user
        cls.user = cls.env.ref("base.user_demo")
        cls.user.write(
            {"groups_id": [(4, cls.env.ref("storage_image.group_image_manager").id)]}
        )
        cls.env = cls.env(user=cls.user)
        # Storage backend
        cls.backend = cls.env.ref("storage_backend.default_storage_backend")

    @classmethod
    def _get_file_content(cls, name, base_path=None):
        path = base_path or cls.base_path
        with open(os.path.join(path, name), "rb") as f:
            data = f.read()
        return data

    @classmethod
    def _create_storage_image(cls, filename, data):
        return cls.env["storage.image"].create({"name": filename, "data": data})

    @classmethod
    def _create_storage_image_from_file(cls, filename, base_path=None):
        data = cls._get_file_content(filename, base_path=base_path)
        data = base64.b64encode(data)
        return cls._create_storage_image(os.path.basename(filename), data)

    def _check_thumbnail(self, image):
        self.assertEqual(len(image.thumbnail_ids), 2)
        medium = image._get_thumb("medium")
        small = image._get_thumb("small")
        self.assertEqual(medium.size_x, 128)
        self.assertEqual(medium.size_y, 128)
        self.assertEqual(small.size_x, 64)
        self.assertEqual(small.size_y, 64)
