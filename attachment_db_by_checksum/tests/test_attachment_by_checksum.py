#  Copyright 2023 Simone Rubino - TAKOBI
#  License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import base64

from odoo.tests import SavepointCase

from odoo.addons.attachment_db_by_checksum.models.ir_attachment import (
    HASHED_STORAGE_PARAMETER,
)


class TestAttachmentByChecksum(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.data = b"Test attachment data"
        cls.attachment = cls.env["ir.attachment"].create(
            {
                "name": "Test attachment",
                "datas": base64.b64encode(cls.data),
            }
        )
        # Save the fname (a2/a2...) of the attachment
        # so that we can use it in tests where the attachment is deleted
        cls.fname = cls.attachment.store_fname

    @classmethod
    def _set_hashed_db_storage(cls):
        """Set `hashed_db` Attachment Storage."""
        cls.env["ir.config_parameter"].set_param(
            "ir_attachment.location",
            HASHED_STORAGE_PARAMETER,
        )

    def test_force_storage(self):
        """Move storage from default to `hashed_db`:
        attachments are copied in `Attachment content by hash` records.
        """
        # Arrange: Create an attachment
        data = self.data
        fname = self.fname
        attachment = self.attachment
        # pre-condition: The storage is not `hashed_db`
        self.assertNotEqual(
            self.env["ir.attachment"]._storage(), HASHED_STORAGE_PARAMETER
        )
        self.assertEqual(attachment.raw, data)

        # Act: Move the storage
        self._set_hashed_db_storage()
        self.env["ir.attachment"].force_storage()

        # Assert: The attachment value is both in the attachment
        # and in the Attachment content by hash
        self.assertEqual(self.env["ir.attachment"]._storage(), HASHED_STORAGE_PARAMETER)
        self.assertEqual(attachment.raw, data)
        attachment_content = self.env["ir.attachment.content"].search_by_checksum(fname)
        self.assertEqual(attachment_content.db_datas, data)

    def test_new_hashed_attachment(self):
        """Storage is `hashed_db`:
        new attachments are only stored in `Attachment content by hash` records.
        """
        # Arrange: Set the storage to `hashed_db`
        data = self.data
        fname = self.fname
        self.attachment.unlink()
        self._set_hashed_db_storage()
        # pre-condition
        self.assertEqual(self.env["ir.attachment"]._storage(), HASHED_STORAGE_PARAMETER)

        # Act: Create an attachment
        self.env["ir.attachment"].create(
            {
                "name": "Test attachment",
                "datas": base64.b64encode(data),
            }
        )

        # Assert: The new attachment value is in the Attachment content by hash
        self.assertEqual(self.env["ir.attachment"]._storage(), HASHED_STORAGE_PARAMETER)
        attachment_content = self.env["ir.attachment.content"].search_by_checksum(fname)
        self.assertEqual(attachment_content.db_datas, data)

    def test_force_storage_invisible_menu(self):
        """Move storage from default to `hashed_db`:
        attachments linked to invisible menus
        are copied in `Attachment content by hash` records.
        """
        # Arrange: Create a menu invisible for current user
        fname = self.fname
        self.attachment.unlink()
        menu_model = self.env["ir.ui.menu"]
        invisible_menu = menu_model.create(
            {
                "name": "Test invisible menu",
                "web_icon_data": base64.b64encode(self.data),
                "groups_id": [(6, 0, self.env.ref("base.group_no_one").ids)],
            }
        )
        # pre-condition: The menu is invisible and storage is not `hashed_db`
        self.assertNotEqual(
            self.env["ir.attachment"]._storage(), HASHED_STORAGE_PARAMETER
        )
        self.assertNotIn(invisible_menu, menu_model.search([]))

        # Act: Move the storage to `hashed_db`
        self._set_hashed_db_storage()
        self.env["ir.attachment"].with_user(
            self.env.ref("base.user_admin")
        ).force_storage()

        # Assert: The menu's attachment value is in the Attachment content by hash
        self.assertEqual(self.env["ir.attachment"]._storage(), HASHED_STORAGE_PARAMETER)
        attachment_content = self.env["ir.attachment.content"].search_by_checksum(fname)
        self.assertTrue(attachment_content)
