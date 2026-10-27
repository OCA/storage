# Copyright 2026 Camptocamp SA
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64

from odoo.exceptions import UserError

from odoo.addons.component.tests.common import TransactionComponentCase


class TestReplaceFile(TransactionComponentCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend = cls.env.ref("storage_backend.default_storage_backend")
        cls.backend.filename_strategy = "hash"
        cls.data_1 = base64.b64encode(b"file 1")
        cls.data_2 = base64.b64encode(b"file 2")
        cls.current_file = cls._create_file("current.txt", cls.data_2)

    @classmethod
    def _create_file(cls, name, data):
        return cls.env["storage.file"].create(
            {"name": name, "backend_id": cls.backend.id, "data": data}
        )

    def _get_file_from_data(self, data, file_name="new.txt"):
        wiz = self.env["storage.file.replace"].create(
            {"file_id": self.current_file.id, "data": data, "file_name": file_name}
        )
        return wiz._get_file_from_data()

    def test_new_content(self):
        """New content is stored in a new file."""
        new_file = self._get_file_from_data(self.data_1)
        self.assertNotEqual(new_file, self.current_file)
        self.assertEqual(new_file.data, self.data_1)

    def test_reuse_file_to_delete(self):
        """A file waiting for deletion with the same content is reused."""
        old_file = self._create_file("old.txt", self.data_1)
        old_file.unlink()
        self.assertTrue(old_file.to_delete)
        new_file = self._get_file_from_data(self.data_1)
        self.assertEqual(new_file, old_file)
        self.assertFalse(new_file.to_delete)
        self.assertTrue(new_file.active)
        self.assertEqual(new_file.name, "new.txt")
        self.assertEqual(new_file.data, self.data_1)

    def test_same_content_as_current(self):
        """Uploading the current content again is refused."""
        with self.assertRaisesRegex(
            UserError, "The new file is identical to the current one."
        ):
            self._get_file_from_data(self.data_2)

    def test_same_content_stored(self):
        """Content already stored by a file in use is refused."""
        other_file = self._create_file("other.txt", self.data_1)
        other_file.active = False
        with self.assertRaises(UserError) as err:
            self._get_file_from_data(self.data_1)
        self.assertEqual(
            str(err.exception),
            "The same content is already stored in file 'other.txt' "
            f"(ID {other_file.id}).",
        )

    def test_name_with_id_strategy(self):
        """Without the 'hash' strategy, the same content is stored again."""
        self.backend.filename_strategy = "name_with_id"
        new_file = self._get_file_from_data(self.data_2)
        self.assertNotEqual(new_file, self.current_file)
        self.assertEqual(new_file.data, self.data_2)
