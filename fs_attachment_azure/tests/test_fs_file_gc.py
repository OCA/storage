# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from types import SimpleNamespace
from unittest.mock import patch

from odoo.addons.fs_attachment_azure.models.fs_storage import (
    AZURE_MAX_BLOBS_PER_BATCH,
)

from .common import TestFSAttachmentAzureCommon

CONTAINER = "test-blob"


class FakeBatchResponses:
    """Async iterator of subresponses, as ``delete_blobs`` returns one."""

    def __init__(self, status_codes):
        self._status_codes = list(status_codes)

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self._status_codes:
            raise StopAsyncIteration
        return SimpleNamespace(status_code=self._status_codes.pop(0))


class FakeContainerClient:
    """Minimal stand-in for an asynchronous ContainerClient."""

    def __init__(self, status_codes=None, error=None):
        # blob name -> status code to answer, anything else is deleted (202)
        self.status_codes = status_codes or {}
        self.error = error
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return None

    async def delete_blobs(self, *blobs, **kwargs):
        self.calls.append((blobs, kwargs))
        if self.error:
            raise self.error
        return FakeBatchResponses([self.status_codes.get(blob, 202) for blob in blobs])


class FakeServiceClient:
    def __init__(self, container_client):
        self.container_client = container_client
        self.container_names = []

    def get_container_client(self, container_name):
        self.container_names.append(container_name)
        return self.container_client


class TestFsFileGcAzure(TestFSAttachmentAzureCommon):
    def setUp(self):
        super().setUp()
        self.gc_file_model = self.env["fs.file.gc"]

    def _mark_for_gc(self, *store_fnames):
        for store_fname in store_fnames:
            self.gc_file_model._mark_for_gc(store_fname)

    def _gc_azure_bulk_delete(self, container_client):
        """Run the bulk delete against a fake Azure container."""
        root_fs = SimpleNamespace(service_client=FakeServiceClient(container_client))
        storage_class = type(self.azure_backend)
        code = self.azure_backend.code
        with patch.object(
            storage_class,
            "is_azure_storage",
            new=property(lambda storage: storage.code == code),
        ), patch.object(storage_class, "_get_root_filesystem", return_value=root_fs):
            self.gc_file_model._gc_azure_bulk_delete()
        return root_fs.service_client

    def _gc_rows(self, *store_fnames):
        return self.gc_file_model.search(
            [("store_fname", "in", list(store_fnames))]
        ).mapped("store_fname")

    def test_batch_size_is_azure_limit(self):
        """A batch cannot hold more blobs than Azure accepts."""
        self.assertEqual(self.gc_file_model._GC_BATCH_SIZE, AZURE_MAX_BLOBS_PER_BATCH)
        self.assertEqual(AZURE_MAX_BLOBS_PER_BATCH, 256)

    def test_delete_blobs_rejects_oversized_batch(self):
        """The storage refuses more blobs than a batch request can hold."""
        blob_names = [f"blob_{i}" for i in range(AZURE_MAX_BLOBS_PER_BATCH + 1)]
        with self.assertRaises(ValueError):
            self.azure_backend._azure_delete_blobs(blob_names)

    def test_delete_blobs_without_blobs_sends_no_request(self):
        """Nothing to delete means no request at all."""
        self.assertEqual(self.azure_backend._azure_delete_blobs([]), [])

    def test_bulk_delete_removes_orphaned_files(self):
        """Orphaned blobs are deleted in one request, referenced ones are kept."""
        orphan_1 = "azure://dir/sub/orphan_1.txt"
        orphan_2 = "azure://dir/sub/orphan_2.txt"
        referenced = self.fake_attachment_azure.store_fname
        self._mark_for_gc(orphan_1, orphan_2, referenced)

        container_client = FakeContainerClient()
        service_client = self._gc_azure_bulk_delete(container_client)

        self.assertEqual(len(container_client.calls), 1)
        blobs, kwargs = container_client.calls[0]
        self.assertCountEqual(blobs, ["dir/sub/orphan_1.txt", "dir/sub/orphan_2.txt"])
        self.assertFalse(
            kwargs["raise_on_any_failure"],
            "One blob that cannot be deleted must not discard the batch.",
        )
        self.assertEqual(service_client.container_names, [CONTAINER])
        self.assertEqual(self._gc_rows(orphan_1, orphan_2, referenced), [referenced])

    def test_bulk_delete_collects_missing_blobs(self):
        """A blob that is already gone is collected as if it was deleted."""
        orphan = "azure://dir/sub/orphan.txt"
        self._mark_for_gc(orphan)

        container_client = FakeContainerClient(status_codes={"dir/sub/orphan.txt": 404})
        self._gc_azure_bulk_delete(container_client)

        self.assertFalse(self._gc_rows(orphan))

    def test_bulk_delete_keeps_rows_of_failed_blobs(self):
        """A blob that Azure refuses to delete is left to the file by file pass."""
        deleted = "azure://dir/sub/deleted.txt"
        failed = "azure://dir/sub/failed.txt"
        self._mark_for_gc(deleted, failed)

        container_client = FakeContainerClient(status_codes={"dir/sub/failed.txt": 500})
        self._gc_azure_bulk_delete(container_client)

        # A partial failure must not loop on the rows it cannot delete.
        self.assertEqual(len(container_client.calls), 1)
        self.assertEqual(self._gc_rows(deleted, failed), [failed])

    def test_bulk_delete_keeps_rows_when_request_fails(self):
        """A failing request is logged and leaves every row in place."""
        orphan = "azure://dir/sub/orphan.txt"
        self._mark_for_gc(orphan)

        container_client = FakeContainerClient(error=Exception("Azure is unavailable"))
        with self.assertLogs(
            "odoo.addons.fs_attachment_azure.models.fs_file_gc", level="ERROR"
        ):
            self._gc_azure_bulk_delete(container_client)

        self.assertEqual(self._gc_rows(orphan), [orphan])

    def test_bulk_delete_sends_one_request_per_batch(self):
        """More orphans than a batch holds are deleted in several requests."""
        orphans = [f"azure://dir/sub/orphan_{i}.txt" for i in range(3)]
        self._mark_for_gc(*orphans)

        container_client = FakeContainerClient()
        with patch.object(type(self.gc_file_model), "_GC_BATCH_SIZE", 2):
            self._gc_azure_bulk_delete(container_client)

        self.assertEqual(
            [len(blobs) for blobs, _kwargs in container_client.calls], [2, 1]
        )
        self.assertFalse(self._gc_rows(*orphans))

    def test_bulk_delete_ignores_storages_without_autovacuum(self):
        """A storage with the autovacuum disabled is not collected."""
        self.azure_backend.autovacuum_gc = False
        orphan = "azure://dir/sub/orphan.txt"
        self._mark_for_gc(orphan)

        container_client = FakeContainerClient()
        self._gc_azure_bulk_delete(container_client)

        self.assertFalse(container_client.calls)
        self.assertEqual(self._gc_rows(orphan), [orphan])
