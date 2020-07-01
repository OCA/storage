# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os

from openerp import _
from openerp.addons.component.core import Component
from openerp.exceptions import AccessError
import urllib


def is_safe_path(basedir, path):
    return os.path.realpath(path).startswith(basedir)


class HttpStorageBackend(Component):
    _name = "filesystem.adapter"
    _inherit = "base.storage.adapter"
    _usage = "http"

    def add(self, relative_path, data, **kwargs):
        raise UserError(_("http backend do not support adding element"))

    def get(self, relative_path, **kwargs):
        # TODO fixme in 12 (se do not have the base_url here)
        full_path = os.path.join(self.collection.base_url, relative_path)
        return urllib.request.urlopen(full_path).read()

    def list(self, relative_path=""):
        raise UserError(_("http backend do not support listing element"))

    def delete(self, relative_path):
        pass
