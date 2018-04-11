# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.tests.common import TransactionComponentCase
import base64


class Common(TransactionComponentCase):

    def setUp(self):
        super(Common, self).setUp()
        self.filedata = base64.b64encode('This is a simple file')
        self.filename = 'test_file.txt'
