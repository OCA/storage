# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging
import os
import re
from openerp import fields, models
logger = logging.getLogger(__name__)


class FileStoreStorageBackend(models.Model):
    _inherit = 'storage.backend'

    backend_type = fields.Selection(
        selection_add=[('filestore', 'Filestore')])

    filestore_public_base_url = fields.Char(
        sparse="data")
    filestore_base_path = fields.Char(
        sparse="data")

    def _fullpath(self, name):
        """This will build the full path for the file, we force to
        store the data inside the filestore in the directory 'storage".
        Becarefull if you implement your own custom path, end user
        should never be able to write or read unwanted filesystem file"""
        # sanitize base_path
        base_path = re.sub('[.]', '', self.filestore_base_path).strip('/\\')
        # sanitize name
        name = name.strip('/\\')
        return os.path.join(
            self.env['ir.attachment']._filestore(), 'storage', base_path, name)

    def _filestore_store(self, name, datas, is_public=False):
        full_path = self._fullpath(name)
        dirname = os.path.dirname(full_path)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        logger.debug('Backend Storage: Write file %s to filestore', full_path)
        with open(full_path, "wb") as my_file:
            my_file.write(datas)
        return name

    def _filestoreget_public_url(self, name):
        return os.path.join(self.filestore_public_base_url, name)

    def _filestoreretrieve_datas(self, name):
        logger.debug('Backend Storage: Read file %s from filestore', name)
        full_path = self._fullpath(name)
        with open(full_path, "b") as my_file:
            datas = my_file.read()
        return datas and base64.b64encode(datas) or False
