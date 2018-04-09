# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.tests.common import TransactionComponentCase
import base64
import urlparse
import os


class StorageImageCase(TransactionComponentCase):

    def setUp(self):
        super(StorageImageCase, self).setUp()
        self.backend = self.env.ref('storage_backend.default_storage_backend')
        path = os.path.dirname(os.path.abspath(__file__))
        f = open(os.path.join(path, 'static/akretion-logo.png'))
        data = f.read()
        self.filesize = len(data)
        self.filedata = base64.b64encode(data)
        self.filename = 'akretion-logo.png'

    def _create_storage_image(self):
        return self.env['storage.image'].create({
            'name': self.filename,
            'datas': self.filedata,
            })

    def test_create_and_read_image(self):
        image = self._create_storage_image()
        self.assertEqual(image.datas, self.filedata)
        self.assertEqual(image.mimetype, u'image/png')
        self.assertEqual(image.extension, u'.png')
        self.assertEqual(image.filename, u'akretion-logo')
        url = urlparse.urlparse(image.url)
        self.assertEqual(
            url.path,
            "/web/content/storage.file/%s/datas" % image.file_id.id)
        self.assertEqual(image.file_size, self.filesize)
        self.assertEqual(self.backend.id, image.backend_id.id)

    def test_create_thumbnail(self):
        image = self._create_storage_image()
        # Check that no thumbnail exist
        self.assertEqual(len(image.thumbnail_ids), 0)

        # Getting thumbnail url should generate small and medium thumbnail
        self.assertIsNotNone(image.image_medium_url)

        # TODO FIXME we should find a way to avoid to clear the env here
        self.env.clear()

        self.assertEqual(len(image.thumbnail_ids), 2)
        medium, small = image.thumbnail_ids
        self.assertEqual(medium.size_x, 128)
        self.assertEqual(medium.size_y, 128)
        self.assertEqual(small.size_x, 64)
        self.assertEqual(small.size_y, 64)
