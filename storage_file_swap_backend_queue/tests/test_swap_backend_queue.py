# Copyright 2026 Camptocamp SA
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
from unittest import mock

from odoo.addons.component.tests.common import TransactionComponentCase
from odoo.addons.queue_job.tests.common import trap_jobs


class TestSwapBackendQueue(TransactionComponentCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend_a = cls.env.ref("storage_backend.default_storage_backend")
        cls.backend_a.swap_backend_use_queue = True
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

    def test_wizard_enqueues_jobs_split_by_batch(self):
        """Wizard dispatches delayed jobs split by batch size (default 5)."""
        files = self.env["storage.file"]
        for i in range(12):
            files |= self._create_storage_file(name=f"file_{i}.txt", data=b"data")
        wiz = (
            self.env["storage.file.swap.backend"]
            .with_context(active_model="storage.file", active_ids=files.ids)
            .create({"dest_backend_id": self.backend_b.id})
        )
        with trap_jobs() as trap:
            wiz.action_apply()
            # 12 files / 5 per batch = 3 jobs
            trap.assert_jobs_count(3)
            # Perform them to verify they actually work
            trap.perform_enqueued_jobs()
        self.assertTrue(all(f.backend_id == self.backend_b for f in files))

    def test_wizard_single_batch(self):
        """A small recordset creates a single job."""
        files = self.env["storage.file"]
        for i in range(3):
            files |= self._create_storage_file(name=f"file_{i}.txt", data=b"data")
        wiz = (
            self.env["storage.file.swap.backend"]
            .with_context(active_model="storage.file", active_ids=files.ids)
            .create({"dest_backend_id": self.backend_b.id})
        )
        with trap_jobs() as trap:
            wiz.action_apply()
            trap.assert_jobs_count(1)

    def test_wizard_batch_size_from_config_param(self):
        """Batch size is read from ir.config_parameter."""
        self.env["ir.config_parameter"].sudo().set_param(
            "storage_file_swap_backend_queue.swap_backend_batch_size", "3"
        )
        self.env.registry.clear_cache()
        files = self.env["storage.file"]
        for i in range(7):
            files |= self._create_storage_file(name=f"file_{i}.txt", data=b"data")
        wiz = (
            self.env["storage.file.swap.backend"]
            .with_context(active_model="storage.file", active_ids=files.ids)
            .create({"dest_backend_id": self.backend_b.id})
        )
        with trap_jobs() as trap:
            wiz.action_apply()
            # 7 files / 3 per batch = 3 jobs
            trap.assert_jobs_count(3)

    def test_job_moves_files_and_returns_summary(self):
        """The job method moves files and returns a text summary."""
        stfile = self._create_storage_file(data=b"payload")
        result = stfile._swap_backend_job(self.backend_b.id)
        self.assertEqual(stfile.backend_id, self.backend_b)
        self.assertIn("Moved (1):", result)
        self.assertIn(stfile.name, result)

    def test_job_deletes_old_file(self):
        """The job deletes the old file directly."""
        stfile = self._create_storage_file(data=b"payload")
        old_path = stfile.relative_path
        stfile._swap_backend_job(self.backend_b.id)
        with self.assertRaises(FileNotFoundError):
            self.backend_a.sudo().get(old_path, binary=True)

    def test_job_skips_already_on_destination(self):
        """Files already on dest backend produce 'Nothing to swap'."""
        stfile = self._create_storage_file(data=b"payload", backend=self.backend_b)
        result = stfile._swap_backend_job(self.backend_b.id)
        self.assertIn("Nothing to swap", result)

    def test_job_handles_missing_record(self):
        """Deleted records between enqueue and execution are reported."""
        stfile = self._create_storage_file(data=b"payload")
        file_id = stfile.id
        stfile.with_context(cleanning_storage_file=True).unlink()
        records = self.env["storage.file"].browse(file_id)
        result = records._swap_backend_job(self.backend_b.id)
        self.assertIn("no longer exists", result)

    def test_job_handles_upload_failure(self):
        """Upload failures are caught and reported."""
        stfile = self._create_storage_file(data=b"payload")
        with mock.patch.object(
            type(self.env["storage.backend"]),
            "add",
            side_effect=RuntimeError("upload failed"),
        ):
            result = stfile._swap_backend_job(self.backend_b.id)
        self.assertIn("Failed (1):", result)
        self.assertIn("upload failed", result)

    def test_job_handles_missing_backend(self):
        """If dest backend is deleted, the job returns an error message."""
        stfile = self._create_storage_file(data=b"payload")
        result = stfile._swap_backend_job(99999)
        self.assertIn("no longer exists", result)

    def test_job_old_delete_failure_still_counts_as_moved(self):
        """Failure to delete old file doesn't prevent success."""
        stfile = self._create_storage_file(data=b"payload")
        with mock.patch.object(
            type(self.env["storage.backend"]),
            "delete",
            side_effect=RuntimeError("delete failed"),
        ):
            result = stfile._swap_backend_job(self.backend_b.id)
        self.assertIn("Moved (1):", result)
        self.assertEqual(stfile.backend_id, self.backend_b)

    def test_wizard_use_queue_flag_from_backend(self):
        """Wizard use_queue is preset from source backend flag."""
        stfile = self._create_storage_file(data=b"payload")
        wiz = (
            self.env["storage.file.swap.backend"]
            .with_context(active_model="storage.file", active_ids=stfile.ids)
            .create({"dest_backend_id": self.backend_b.id})
        )
        self.assertTrue(wiz.use_queue)
        # Disable queue on source backend
        self.backend_a.swap_backend_use_queue = False
        wiz2 = (
            self.env["storage.file.swap.backend"]
            .with_context(active_model="storage.file", active_ids=stfile.ids)
            .create({"dest_backend_id": self.backend_b.id})
        )
        self.assertFalse(wiz2.use_queue)

    def test_wizard_sync_when_queue_disabled(self):
        """When use_queue is False, swap runs synchronously."""
        self.backend_a.swap_backend_use_queue = False
        stfile = self._create_storage_file(data=b"payload")
        wiz = (
            self.env["storage.file.swap.backend"]
            .with_context(active_model="storage.file", active_ids=stfile.ids)
            .create({"dest_backend_id": self.backend_b.id})
        )
        with trap_jobs() as trap:
            wiz.action_apply()
            trap.assert_jobs_count(0)
        self.assertEqual(stfile.backend_id, self.backend_b)
