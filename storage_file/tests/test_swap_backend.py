# Copyright 2026 Camptocamp SA
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
from unittest import mock

from odoo.exceptions import UserError
from odoo.tests import Form

from odoo.addons.component.tests.common import TransactionComponentCase


class TestSwapBackend(TransactionComponentCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend_a = cls.env.ref("storage_backend.default_storage_backend")
        cls.backend_b = cls.backend_a.copy(
            {
                "name": "Second Backend",
                "directory_path": "backend_b",
            }
        )
        cls.backend_b.filename_strategy = "name_with_id"

    def _create_storage_file(self, name="my_file.txt", data=b"hello", backend=None):
        return self.env["storage.file"].create(
            {
                "name": name,
                "backend_id": (backend or self.backend_a).id,
                "data": base64.b64encode(data),
            }
        )

    # -- model-level swap -------------------------------------------------

    def test_swap_uploads_to_new_backend_and_updates_record(self):
        stfile = self._create_storage_file(data=b"payload")

        result = stfile._swap_backend(self.backend_b)

        self.assertEqual(stfile.backend_id, self.backend_b)
        self.assertEqual(stfile.relative_path, f"my_file-{stfile.id}.txt")
        self.assertEqual(base64.b64decode(stfile.data), b"payload")
        self.assertIn(stfile.name, result["moved"][0])

    def test_swap_deletes_old_file(self):
        stfile = self._create_storage_file(data=b"payload")
        old_relative_path = stfile.relative_path
        stfile._swap_backend(self.backend_b)
        with self.assertRaises(FileNotFoundError):
            self.backend_a.sudo().get(old_relative_path, binary=True)

    def test_swap_skips_records_already_on_destination(self):
        stfile = self._create_storage_file(backend=self.backend_b)
        with mock.patch.object(
            type(self.env["storage.backend"]), "delete"
        ) as mocked_delete:
            result = stfile._swap_backend(self.backend_b)
            mocked_delete.assert_not_called()
        self.assertEqual(stfile.backend_id, self.backend_b)
        self.assertEqual(result["moved"], [])
        self.assertEqual(result["failed"], [])

    def test_swap_requires_destination(self):
        stfile = self._create_storage_file()
        with self.assertRaisesRegex(UserError, "A destination storage is required"):
            stfile._swap_backend(self.env["storage.backend"])

    def test_swap_requires_destination_filename_strategy(self):
        self.backend_b.filename_strategy = False
        stfile = self._create_storage_file()
        with self.assertRaisesRegex(UserError, "The filename strategy is empty"):
            stfile._swap_backend(self.backend_b)

    def test_swap_failure_reports_in_failed(self):
        """Upload failure is caught and reported in the failed list."""
        stfile = self._create_storage_file(data=b"payload")
        old_relative_path = stfile.relative_path
        with mock.patch.object(
            type(self.env["storage.backend"]),
            "add",
            side_effect=RuntimeError("boom"),
        ):
            result = stfile._swap_backend(self.backend_b)
        self.assertEqual(len(result["failed"]), 1)
        self.assertIn("boom", result["failed"][0])
        # Old file still physically present.
        self.assertEqual(
            self.backend_a.sudo().get(old_relative_path, binary=True), b"payload"
        )

    def test_swap_swallows_old_backend_delete_error(self):
        stfile = self._create_storage_file(data=b"payload")
        with mock.patch.object(
            type(self.env["storage.backend"]),
            "delete",
            side_effect=RuntimeError("boom"),
        ):
            with self.assertLogs(
                "odoo.addons.storage_file.models.storage_file", level="WARNING"
            ) as log_cm:
                result = stfile._swap_backend(self.backend_b)
        self.assertTrue(
            any(
                "Failed to delete" not in msg or "boom" not in msg
                for msg in log_cm.output
            )
            or any("boom" in msg for msg in log_cm.output),
            log_cm.output,
        )
        # File still counts as moved
        self.assertEqual(len(result["moved"]), 1)

    # -- wizard ----------------------------------------------------------------

    def test_wizard_default_get_single_backend(self):
        stfile1 = self._create_storage_file(name="f1.txt")
        stfile2 = self._create_storage_file(name="f2.txt")
        wiz = (
            self.env["storage.file.swap.backend"]
            .with_context(
                active_model="storage.file",
                active_ids=[stfile1.id, stfile2.id],
            )
            .create({})
        )
        self.assertEqual(wiz.source_backend_id, self.backend_a)
        self.assertEqual(wiz.file_ids, stfile1 + stfile2)

    def test_wizard_default_get_rejects_mixed_backends(self):
        stfile1 = self._create_storage_file(name="f1.txt")
        stfile2 = self._create_storage_file(name="f2.txt", backend=self.backend_b)
        with self.assertRaisesRegex(
            UserError,
            "All selected records must belong to the same source storage backend",
        ):
            self.env["storage.file.swap.backend"].with_context(
                active_model="storage.file",
                active_ids=[stfile1.id, stfile2.id],
            ).create({})

    def test_wizard_apply_swaps_files(self):
        stfile = self._create_storage_file(data=b"payload")
        wiz = (
            self.env["storage.file.swap.backend"]
            .with_context(
                active_model="storage.file",
                active_ids=stfile.ids,
            )
            .create({"dest_backend_id": self.backend_b.id})
        )
        wiz.action_apply()
        self.assertEqual(stfile.backend_id, self.backend_b)

    def test_wizard_apply_rejects_same_backend(self):
        stfile = self._create_storage_file()
        wiz = (
            self.env["storage.file.swap.backend"]
            .with_context(
                active_model="storage.file",
                active_ids=stfile.ids,
            )
            .create({})
        )
        wiz.dest_backend_id = wiz.source_backend_id
        with self.assertRaisesRegex(
            UserError, "Destination storage must differ from source"
        ):
            wiz.action_apply()

    def test_wizard_form_loads_with_source_backend(self):
        """The form view loads and pre-fills source_backend_id."""
        stfile = self._create_storage_file()
        view = "storage_file.storage_file_swap_backend_view_form"
        with Form(
            self.env["storage.file.swap.backend"].with_context(
                active_model="storage.file",
                active_ids=stfile.ids,
            ),
            view=view,
        ) as wiz_form:
            self.assertEqual(wiz_form.source_backend_id, self.backend_a)
            wiz_form.dest_backend_id = self.backend_b

    # -- write triggers swap ------------------------------------------------

    def test_write_backend_id_triggers_swap(self):
        """Writing backend_id on storage.file triggers the full swap."""
        stfile = self._create_storage_file(data=b"payload")
        old_path = stfile.relative_path
        stfile.backend_id = self.backend_b
        self.assertEqual(stfile.backend_id, self.backend_b)
        self.assertEqual(base64.b64decode(stfile.data), b"payload")
        with self.assertRaises(FileNotFoundError):
            self.backend_a.sudo().get(old_path, binary=True)

    def test_write_backend_id_noop_if_same(self):
        """Writing same backend_id does nothing special."""
        stfile = self._create_storage_file(data=b"payload")
        old_path = stfile.relative_path
        stfile.backend_id = self.backend_a
        self.assertEqual(stfile.backend_id, self.backend_a)
        self.assertEqual(stfile.relative_path, old_path)
