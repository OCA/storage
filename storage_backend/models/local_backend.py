# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import hashlib
import logging
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
        full_path = self.filestore_base_path + '/' + name
        with open(full_path, "wb") as my_file:
            my_file.write(datas)
        return name

    def _filestoreget_public_url(self, name):
        # TODO faire mieux
        logger.info('get_public_url')
        return self.filestore_public_base_url + '/' + name

    def _filestoreget_base64(self, file_id):
        logger.info('return base64 of a file')
        with OSFS(self.filestore_base_path) as the_dir:
            return the_dir.open(file_id.url).read()
