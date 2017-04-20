# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
import hashlib
from fs.osfs import OSFS
import logging
logger = logging.getLogger(__name__)


class LocalStorageBackend(models.Model):
    _inherit = 'storage.backend'

    public_base_url = fields.Char()
    base_path = u'~/images'

    def store(self, blob, vals={}, object_type=None):
        # TODO: refactorer, ça marche plus vraiment
        # enregistre le binary la où on lui dit
        # renvois l'objet en question
        checksum = u'' + hashlib.sha1(blob).hexdigest()
        path = checksum

        with OSFS(self.base_path) as the_dir:
            the_dir.settext(path, blob)
            size = the_dir.getsize(path)

        basic_vals = {
            # 'name': '',
            'url': path,
            'file_size': size,
            'checksum': checksum,
            'backend_id': self.id,
        }
        return basic_vals
        # vals.update(basic_vals)
        # obj = object_type.create(vals)  # ou déléguer?
        # return obj

    def get_public_url(self, obj):
        # TODO faire mieux
        logger.info('get_public_url')
        return self.public_base_url + '/' + obj.name

    def get_base64(self, file_id):
        logger.info('return base64 of a file')
        with OSFS(self.base_path) as the_dir:
            return the_dir.getbytes(file_id.url)
