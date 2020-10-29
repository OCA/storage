# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError

from .common import CommonCase, BackendStorageTestMixin


class FileSystemCase(CommonCase, BackendStorageTestMixin):

    def test_setting_and_getting_data_from_root(self):
        self._test_setting_and_getting_data_from_root()

    def test_setting_and_getting_data_from_dir(self):
        self._test_setting_and_getting_data_from_dir()


class FileSystemDemoUserAccessCase(CommonCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend = cls.backend.with_user(cls.demo_user)

    def test_cannot_add_file(self):
        with self.assertRaises(AccessError):
            self.backend._add_b64_data(
                self.filename, self.filedata, mimetype=u"text/plain"
            )

    def test_cannot_list_file(self):
        with self.assertRaises(AccessError):
            self.backend._list()

    def test_cannot_read_file(self):
        with self.assertRaises(AccessError):
            self.backend._get_b64_data(self.filename)

    def test_cannot_delete_file(self):
        with self.assertRaises(AccessError):
            self.backend._delete(self.filename)

