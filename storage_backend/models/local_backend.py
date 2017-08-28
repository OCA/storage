# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging
import os
from openerp import fields, models
from openerp.exceptions import AccessError
from openerp.tools.translate import _
logger = logging.getLogger(__name__)


def is_safe_path(basedir, path):
    return os.path.realpath(path).startswith(basedir)


class FileStoreStorageBackend(models.Model):
    _inherit = 'storage.backend'

    backend_type = fields.Selection(
        selection_add=[('filestore', 'Filestore')])

    filestore_public_base_url = fields.Char(
        sparse="data")
    filestore_base_path = fields.Char(
        sparse="data")

    def _basedir(self):
        return os.path.join(self.env['ir.attachment']._filestore(), 'storage')

    def _fullpath(self, name):
        """This will build the full path for the file, we force to
        store the data inside the filestore in the directory 'storage".
        Becarefull if you implement your own custom path, end user
        should never be able to write or read unwanted filesystem file"""
        base_dir = self._basedir()
        full_path = os.path.join(base_dir, self.filestore_base_path, name)
        if not is_safe_path(base_dir, full_path):
            raise AccessError(_("Access to %s is forbidden" % full_path))
        return full_path

    def _filestore_store_data(self, name, datas, is_public=False):
        full_path = self._fullpath(name)
        dirname = os.path.dirname(full_path)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        logger.debug('Backend Storage: Write file %s to filestore', full_path)
        with open(full_path, "wb") as my_file:
            my_file.write(datas)
        return name

    def _filestore_get_public_url(self, name):
        return os.path.join(self.filestore_public_base_url, name)

    def _filestore_retrieve_datas(self, name):
        logger.debug('Backend Storage: Read file %s from filestore', name)
        full_path = self._fullpath(name)
        with open(full_path, "b") as my_file:
            datas = my_file.read()
        return datas and base64.b64encode(datas) or False
