# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError

from .common import Common, GenericStoreCase


class FileSystemCase(Common, GenericStoreCase):
    def test_demo_user_can_not_use_storage(self):
        # Demo user do not have the access right
        self.user = self.env.ref("base.user_demo")
        self.env = self.env(user=self.user)
        self.backend = self.env.ref("storage_backend.default_storage_backend")
        with self.assertRaises(AccessError):
            self._test_setting_and_getting_data()
