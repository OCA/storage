# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from psycopg2 import IntegrityError

from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestImageTag(TransactionCase):
    def test_tech_name_from_name(self):
        """The technical name defaults to the normalized name."""
        tag = self.env["image.tag"].create({"name": "My Nice Tag"})
        self.assertEqual(tag.tech_name, "my_nice_tag")

    def test_tech_name_explicit(self):
        """An explicit technical name is kept."""
        tag = self.env["image.tag"].create({"name": "My Tag", "tech_name": "foo"})
        self.assertEqual(tag.tech_name, "foo")

    def test_tech_name_unique(self):
        """Two tags cannot share the same technical name."""
        self.env["image.tag"].create({"name": "My Tag", "tech_name": "foo"})
        with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError):
            self.env["image.tag"].create({"name": "Other Tag", "tech_name": "foo"})
            self.env.flush_all()
