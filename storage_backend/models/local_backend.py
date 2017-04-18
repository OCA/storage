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

    def store(self, binary, vals, object_type):
        # enregistre le binary la où on lui dit
        # renvois l'objet en question
        file_hash = u'' + hashlib.sha1(binary).hexdigest()
        path = file_hash

        with OSFS(self.base_path) as the_file:
            the_file.settext(path, binary)
            size = the_file.getsize(path)

        basic_vals = {
            'name': '',
            'path': path,
            'size': size,
            'sha1': file_hash,
            'backend_id': self.id,
        }
        obj = object_type.create(basic_vals)
        return obj

    def get_public_url(self, obj):
        logger.info('get_public_url')
        return self.public_base_url + '/' + obj.path
