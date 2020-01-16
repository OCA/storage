# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError

from .common import Common, GenericStoreCase


class FileSystemCase(Common, GenericStoreCase):
    pass


class FileSystemDemoUserAccessCase(Common):
    @classmethod
    def _add_access_right_to_user(cls):
        # We do not give the access to demo user
        # all test should raise an error
        pass

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
