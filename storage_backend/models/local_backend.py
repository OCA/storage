# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import hashlib
import logging
from openerp import fields, models
logger = logging.getLogger(__name__)

try:
    from fs.osfs import OSFS
except ImportError as err:
    logger.debug(err)


class FileStoreStorageBackend(models.Model):
    _inherit = 'storage.backend'

    public_base_url = fields.Char()
    base_path = u'~/images'

    def _filestorestore(self, blob, vals):
        # TODO: refactorer, ça marche plus vraiment
        # enregistre le binary la où on lui dit
        # renvois l'objet en question
        checksum = u'' + hashlib.sha1(blob).hexdigest()
        path = checksum

        with OSFS(self.base_path) as the_dir:
            the_dir.setcontents(path, blob)
            size = the_dir.getsize(path)

        basic_vals = {
            # 'name': '',
            'url': path,
            'file_size': size,
            'checksum': checksum,
            'backend_id': self.id,
            'private_path': path,
        }
        return basic_vals

    def _filestoreget_public_url(self, obj):
        # TODO faire mieux
        logger.info('get_public_url')
        return self.public_base_url + '/' + obj.name

    def _filestoreget_base64(self, file_id):
        logger.info('return base64 of a file')
        with OSFS(self.base_path) as the_dir:
            return the_dir.open(file_id.url).read()
