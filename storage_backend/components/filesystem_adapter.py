# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging
import os
from odoo.exceptions import AccessError
from odoo import _
from odoo.addons.component.core import Component

logger = logging.getLogger(__name__)


def is_safe_path(basedir, path):
    return os.path.realpath(path).startswith(basedir)


class FileSystemStorageBackend(Component):
    _name = 'filesystem.adapter'
    _inherit = 'base.storage.adapter'
    _usage = 'filesystem'

    def _basedir(self):
        return os.path.join(self.env['ir.attachment']._filestore(), 'storage')

    def _fullpath(self, name):
        """This will build the full path for the file, we force to
        store the data inside the filestore in the directory 'storage".
        Becarefull if you implement your own custom path, end user
        should never be able to write or read unwanted filesystem file"""
        base_dir = self._basedir()
        full_path = os.path.join(
            base_dir,
            self.collection.filesystem_base_path or '',
            name)
        if not is_safe_path(base_dir, full_path):
            raise AccessError(_("Access to %s is forbidden" % full_path))
        return full_path

    def store_data(self, name, datas, is_public=False):
        full_path = self._fullpath(name)
        dirname = os.path.dirname(full_path)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        logger.debug('Backend Storage: Write file %s to filesystem', full_path)
        with open(full_path, "wb") as my_file:
            my_file.write(datas)
        return name

    def get_external_url(self, name):
        return os.path.join(
            self.collection.filesystem_public_base_url or '', name)

    def retrieve_data(self, name):
        logger.debug('Backend Storage: Read file %s from filesystem', name)
        full_path = self._fullpath(name)
        with open(full_path, "rb") as my_file:
            datas = my_file.read()
        return datas and base64.b64encode(datas) or False
