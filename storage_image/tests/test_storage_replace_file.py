# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import base64

from odoo.tests import Form

from .common import StorageImageCommonCase


class TestStorageReplaceFile(StorageImageCommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        raw_data_1 = cls._get_file_content("static/akretion-logo.png")
        cls.filesize_1 = len(raw_data_1)
        cls.filedata_1 = base64.b64encode(raw_data_1)
        cls.filename_1 = "akretion-logo.png"
        raw_data_2 = cls._get_file_content("static/oca.png")
        cls.filesize_2 = len(raw_data_2)
        cls.filedata_2 = base64.b64encode(raw_data_2)
        cls.filename_2 = "oca.png"

    def test_wizard_change_file(self):
        image = self._create_storage_image(self.filename_1, self.filedata_1)
        wiz_form = Form(
            self.env["storage.file.replace"].with_context(
                **{"active_model": "storage.image", "active_id": image.id}
            ),
            view="storage_image.storage_file_replace_view_form",
        )
        # Check default_get
        self.assertEqual(wiz_form.image_id, image)
        self.assertEqual(wiz_form.image_id.file_id, image.file_id)
        # Write file name first, as when the file widget is used,
        # a default file name is retrieved from the image that has been picked.
        # We don't have that here.
        wiz_form.file_name = self.filename_2
        wiz_form.data = self.filedata_2
        # Now, confirm the wiz
        wiz = wiz_form.save()
        wiz.confirm()
        # When confirmed, the storage_image points to the new file
        self.assertEqual(image.file_id.name, self.filename_2)
        self.assertEqual(image.file_id.data, self.filedata_2)

        # Now, do revert the change
        wiz_form = Form(
            self.env["storage.file.replace"].with_context(
                **{"active_model": "storage.image", "active_id": image.id}
            )
        )
        wiz_form.file_name = self.filename_1
        wiz_form.data = self.filedata_1
        wiz = wiz_form.save()
        wiz.sudo().confirm()
        # And ensure that the new file
        self.assertEqual(image.file_id.name, self.filename_1)
        self.assertEqual(image.file_id.data, self.filedata_1)
        self.assertEqual(image.file_id.file_type, "image")

    def test_wizard_change_file_keep_history(self):
        image = self._create_storage_image(self.filename_1, self.filedata_1)
        old_file = image.file_id
        wiz_form = Form(
            self.env["storage.file.replace"].with_context(
                **{"active_model": "storage.image", "active_id": image.id}
            ),
            view="storage_image.storage_file_replace_view_form",
        )
        wiz_form.file_name = self.filename_2
        wiz_form.data = self.filedata_2
        wiz_form.keep_history = True
        wiz_form.save().confirm()
        # The image holds the new file and stays active
        self.assertTrue(image.active)
        self.assertEqual(image.file_id.data, self.filedata_2)
        # An archived copy holds the old file, untouched
        archived_image = self.env["storage.image"].search(
            [("file_id", "=", old_file.id), ("active", "=", False)]
        )
        self.assertEqual(len(archived_image), 1)
        self.assertEqual(archived_image.data, self.filedata_1)
        self.assertEqual(archived_image.backend_id, old_file.backend_id)
        self.assertFalse(old_file.to_delete)

    def test_wizard_change_file_no_history(self):
        image = self._create_storage_image(self.filename_1, self.filedata_1)
        old_file = image.file_id
        backend, relative_path = old_file.backend_id, old_file.relative_path
        wiz_form = Form(
            self.env["storage.file.replace"].with_context(
                **{"active_model": "storage.image", "active_id": image.id}
            ),
            view="storage_image.storage_file_replace_view_form",
        )
        wiz_form.file_name = self.filename_2
        wiz_form.data = self.filedata_2
        wiz_form.keep_history = False
        wiz_form.save().confirm()
        self.assertTrue(image.active)
        self.assertEqual(image.file_id.data, self.filedata_2)
        # Nothing refers to the old file anymore: it is deleted
        self.assertFalse(old_file.exists())
        self.assertNotIn(relative_path, backend.list_files())
