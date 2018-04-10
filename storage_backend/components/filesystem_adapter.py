# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import os
from odoo.exceptions import AccessError
from odoo import _
from odoo.addons.component.core import Component


def is_safe_path(basedir, path):
    return os.path.realpath(path).startswith(basedir)


class FileSystemStorageBackend(Component):
    _name = 'filesystem.adapter'
    _inherit = 'base.storage.adapter'
    _usage = 'filesystem'

    def _basedir(self):
        return os.path.join(self.env['ir.attachment']._filestore(), 'storage')

    def _fullpath(self, relative_path):
        """This will build the full path for the file, we force to
        store the data inside the filestore in the directory 'storage".
        Becarefull if you implement your own custom path, end user
        should never be able to write or read unwanted filesystem file"""
        base_dir = self._basedir()
        full_path = os.path.join(
            base_dir,
            self.collection.directory_path or '',
            relative_path)
        if not is_safe_path(base_dir, full_path):
            raise AccessError(_("Access to %s is forbidden" % full_path))
        return full_path

    def store_data(self, relative_path, datas, is_public=False):
        full_path = self._fullpath(relative_path)
        dirname = os.path.dirname(full_path)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        with open(full_path, "wb") as my_file:
            my_file.write(datas)

    def retrieve_data(self, relative_path):
        full_path = self._fullpath(relative_path)
        with open(full_path, "rb") as my_file:
            datas = my_file.read()
        return datas and base64.b64encode(datas) or False
