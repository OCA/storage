# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging
import os
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

    def _filestore_store(self, name, datas, is_public=False):
        # TODO: refactorer, ça marche plus vraiment
        # enregistre le binary la où on lui dit
        # renvois l'objet en question
        full_path = os.path.join(self.filestore_base_path, name)
        with open(full_path, "wb") as my_file:
            my_file.write(datas)
        return name

    def _filestoreget_public_url(self, name):
        # TODO faire mieux
        logger.info('get_public_url')
        return os.path.join(self.filestore_public_base_url, name)

    def _filestoreretrieve_datas(self, name):
        logger.info('return base64 of a file')
        full_path = os.path.join(self.filestore_base_path, name)
        with open(full_path, "b") as my_file:
            datas = my_file.read()
        return datas and base64.b64encode(datas) or False
