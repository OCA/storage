# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent
import base64


class BaseStorageAdapter(AbstractComponent):
    _name = 'base.storage.adapter'
    _collection = 'storage.backend'

    def store(self, name, datas, is_base64=True, **kwargs):
        if is_base64:
            datas = base64.b64decode(datas)
        return self.store_data(name, datas, **kwargs)

    def store_data(self, name, datas, **kwargs):
        raise NotImplemented

    def get_external_url(self, name, **kwargs):
        raise NotImplemented

    def retrieve_data(self, name, **kwargs):
        raise NotImplemented
