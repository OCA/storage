# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import base64

from odoo.tests.common import Form

from odoo.addons.component.tests.common import TransactionComponentCase


class TestX(TransactionComponentCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.filedata_1 = base64.b64encode(b"file 1")
        cls.filename_1 = "test_file_1.txt"
        cls.filedata_2 = base64.b64encode(b"file 2")
        cls.filename_2 = "test_file_2.txt"

    def test_wizard_change_file(self):
        media = self.env["storage.media"].create(
            {
                "name": self.filename_1,
                "data": self.filedata_1,
            }
        )
        wiz_form = Form(
            self.env["storage.file.replace"].with_context(
                {"active_model": "storage.media", "active_id": media.id}
            ),
            view="storage_media.storage_file_replace_view_form",
        )
        # Check default_get
        self.assertEqual(wiz_form.media_id, media)
        self.assertEqual(wiz_form.media_id.file_id, media.file_id)
        # Write file name first, as when the file widget is used,
        # a default file name is retrieved from the media that has been picked.
        # We don't have that here.
        wiz_form.file_name = self.filename_2
        wiz_form.data = self.filedata_2
        # Now, confirm the wiz
        wiz = wiz_form.save()
        wiz.confirm()
        # When confirmed, the storage_media points to the new file
        self.assertEqual(media.file_id.name, self.filename_2)
        self.assertEqual(media.file_id.data, self.filedata_2)

        # Now, do revert the change
        wiz_form = Form(
            self.env["storage.file.replace"].with_context(
                {"active_model": "storage.media", "active_id": media.id}
            )
        )
        wiz_form.file_name = self.filename_1
        wiz_form.data = self.filedata_1
        wiz = wiz_form.save()
        wiz.confirm()
        # And ensure that the new file
        self.assertEqual(media.file_id.name, self.filename_1)
        self.assertEqual(media.file_id.data, self.filedata_1)
