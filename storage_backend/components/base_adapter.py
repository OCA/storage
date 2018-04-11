# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
from odoo.addons.component.core import AbstractComponent


class BaseStorageAdapter(AbstractComponent):
    _name = 'base.storage.adapter'
    _collection = 'storage.backend'

    def _fullpath(self, relative_path):
        if self.collection.directory_path:
            return os.path.join(
                self.collection.directory_path or '', relative_path)
        else:
            return relative_path

    def store_data(self, relative_path, datas, **kwargs):
        raise NotImplemented

    def retrieve_data(self, relative_path, **kwargs):
        raise NotImplemented
