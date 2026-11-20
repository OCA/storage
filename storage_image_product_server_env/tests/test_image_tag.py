# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.tests.common import TransactionCase


class TestImageTag(TransactionCase):
    def test_section_name(self):
        """The server env section is based on the technical name."""
        tag = self.env["image.tag"].create({"name": "My Tag", "tech_name": "my_tag"})
        self.assertEqual(tag._server_env_section_name(), "image_tag.my_tag")
