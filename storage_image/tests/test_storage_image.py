# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.tests.common import TransactionComponentCase
from odoo.exceptions import AccessError
import base64
import urlparse
import os


class StorageImageCase(TransactionComponentCase):

    def setUp(self):
        super(StorageImageCase, self).setUp()
        # Run the test with the demo user in order to check the access right
        self.user = self.env.ref('base.user_demo')
        self.user.write({'groups_id': [
            (4, self.env.ref('storage_image.group_image_manager').id)]})
        self.env = self.env(user=self.user)

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
            'image_medium_url': self.filedata,
            })

    def _check_thumbnail(self, image):
        self.assertEqual(len(image.thumbnail_ids), 2)
        medium, small = image.thumbnail_ids
        self.assertEqual(medium.size_x, 128)
        self.assertEqual(medium.size_y, 128)
        self.assertEqual(small.size_x, 64)
        self.assertEqual(small.size_y, 64)

    def test_create_and_read_image(self):
        image = self._create_storage_image()
        self.assertEqual(image.data, self.filedata)
        self.assertEqual(image.mimetype, u'image/png')
        self.assertEqual(image.extension, u'.png')
        self.assertEqual(image.filename, u'akretion-logo')
        url = urlparse.urlparse(image.url)
        self.assertEqual(
            url.path,
            "/web/content/storage.file/%s/data" % image.file_id.id)
        self.assertEqual(image.file_size, self.filesize)
        self.assertEqual(self.backend.id, image.backend_id.id)

    def test_create_thumbnail(self):
        image = self._create_storage_image()
        # Check that no thumbnail exist
        self.assertEqual(len(image.thumbnail_ids), 0)

        # Getting thumbnail url should generate small and medium thumbnail
        self.assertIsNotNone(image.image_medium_url)
        self._check_thumbnail(image)

    def test_create_thumbnail_with_bin_size(self):
        image = self._create_storage_image()
        # Reading a image can be done with bin_size context
        # this should not impact the generation of thumbnail
        image = image.with_context(bin_size=True)

        # Check that no thumbnail exist
        self.assertEqual(len(image.thumbnail_ids), 0)

        # Getting thumbnail url should generate small and medium thumbnail
        self.assertIsNotNone(image.image_medium_url)
        self._check_thumbnail(image)

    def test_name_onchange(self):
        image = self.env['storage.image'].new({
            'name': 'Test-of image_name.png'})
        image.onchange_name()
        self.assertEqual(image.name, u'test-of-image_name.png')
        self.assertEqual(image.alt_name, u'Test of image name')

    def test_unlink(self):
        image = self._create_storage_image()

        # Generate thumbnail
        self.assertIsNotNone(image.image_medium_url)

        stfile = image.file_id
        thumbnail_files = image.thumbnail_ids.mapped('file_id')
        image.unlink()
        self.assertEqual(stfile.to_delete, True)
        self.assertEqual(stfile.active, False)
        for thumbnail_file in thumbnail_files:
            self.assertEqual(thumbnail_file.to_delete, True)
            self.assertEqual(thumbnail_file.active, False)

    def test_no_manager_user_can_not_write(self):
        # Remove access rigth to demo user
        group_manager = self.env.ref('storage_image.group_image_manager')
        self.user = self.env.ref('base.user_demo')
        self.user.sudo().write({'groups_id': [(3, group_manager.id)]})
        with self.assertRaises(AccessError):
            self._create_storage_image()
