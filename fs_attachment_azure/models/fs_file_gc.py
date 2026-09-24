# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo import models

from .fs_storage import AZURE_MAX_BLOBS_PER_BATCH

_logger = logging.getLogger(__name__)


class FsFileGc(models.Model):
    _inherit = "fs.file.gc"

    # One batch request is sent per iteration, so Azure's own limit is the
    # most files we can handle at once.
    _GC_BATCH_SIZE = AZURE_MAX_BLOBS_PER_BATCH

    def _gc_files_unsafe(self) -> None:
        """Collect the Azure storages by batch before the file by file cleanup.

        Deleting blobs one by one is one request per file, which does not
        scale to a large backlog. Azure deletes up to 256 blobs per request,
        so the Azure storages are collected that way first and ``super()`` is
        left with the rest: the other storages, and the blobs the batch could
        not delete, which it retries one by one.
        """
        self._gc_azure_bulk_delete()
        return super()._gc_files_unsafe()

    def _gc_azure_bulk_delete(self) -> None:
        """Delete the orphaned blobs of every Azure storage, by batch."""
        # autovacuum_gc is not a stored field, so the storages are filtered
        # in memory.
        storages = (
            self.env["fs.storage"]
            .search([])
            .filtered(
                lambda storage: storage.autovacuum_gc and storage.is_azure_storage
            )
        )
        for storage in storages:
            try:
                self._gc_azure_bulk_delete_storage(storage)
            except Exception:
                _logger.exception(
                    "GC: could not batch delete the blobs of the storage %s",
                    storage.code,
                )

    def _gc_azure_bulk_delete_storage(self, storage) -> None:
        """Delete the orphaned blobs of one Azure storage, one batch at a time."""
        while True:
            self._cr.execute(
                """
                SELECT
                    store_fname
                FROM
                    fs_file_gc
                WHERE
                    fs_storage_code = %s
                    AND NOT EXISTS (
                        SELECT 1
                        FROM ir_attachment
                        WHERE store_fname = fs_file_gc.store_fname
                    )
                LIMIT %s
                """,
                (storage.code, self._GC_BATCH_SIZE),
            )
            store_fnames = [row[0] for row in self._cr.fetchall()]
            if not store_fnames:
                return
            blob_names = [
                store_fname.partition("://")[2] for store_fname in store_fnames
            ]
            _logger.info(
                "GC: batch deleting %s blobs of the storage %s",
                len(blob_names),
                storage.code,
            )
            collected = set(storage._azure_delete_blobs(blob_names))
            deleted = [
                store_fname
                for store_fname, blob_name in zip(store_fnames, blob_names, strict=True)
                if blob_name in collected
            ]
            if deleted:
                self._cr.execute(
                    """
                    DELETE FROM
                        fs_file_gc
                    WHERE
                        store_fname = ANY(%s)
                    """,
                    (deleted,),
                )
            if not self._is_test_mode():
                # Commit each batch, so that the progress is kept even if a
                # later batch fails, and the locks taken by _gc_files are not
                # held for the whole backlog.
                self._cr.commit()  # pylint: disable=invalid-commit
            if len(deleted) < len(store_fnames):
                # The blobs that could not be deleted would be selected again
                # by the query above: leave them to the file by file cleanup.
                return
