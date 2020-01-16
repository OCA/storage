# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from odoo.addons.component.tests.common import SavepointComponentCase


class GenericStoreCase(object):
    def _test_setting_and_getting_data(self):
        # Check that the directory is empty
        files = self.backend._list()
        self.assertNotIn(self.filename, files)

        # Add a new file
        self.backend._add_b64_data(self.filename, self.filedata, mimetype=u"text/plain")

        # Check that the file exist
        files = self.backend._list()
        self.assertIn(self.filename, files)

        # Retrieve the file added
        data = self.backend._get_b64_data(self.filename)
        self.assertEqual(data, self.filedata)

        # Delete the file
        self.backend._delete(self.filename)
        files = self.backend._list()
        self.assertNotIn(self.filename, files)

    def test_setting_and_getting_data_from_root(self):
        self._test_setting_and_getting_data()

    def test_setting_and_getting_data_from_dir(self):
        self.backend.directory_path = self.case_with_subdirectory
        self._test_setting_and_getting_data()


class Common(SavepointComponentCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.user = cls.env.ref("base.user_demo")
        cls._add_access_right_to_user()
        cls.env = cls.env(user=cls.user)
        cls.backend = cls.env.ref("storage_backend.default_storage_backend")
        cls.filedata = base64.b64encode(b"This is a simple file")
        cls.filename = "test_file.txt"
        cls.case_with_subdirectory = "subdirectory/here"

    @classmethod
    def _add_access_right_to_user(cls):
        cls.user.write({"groups_id": [(4, cls.env.ref("base.group_system").id)]})
