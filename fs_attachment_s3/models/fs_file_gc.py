# Copyright 2026 APSL-Nagarro Antoni Marroig
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import gc
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class FsFileGc(models.Model):
    _inherit = "fs.file.gc"

    # S3 bulk delete limit is 1000 objects per request
    _S3_GC_BATCH_SIZE = 1000

    def _gc_files_unsafe(self) -> None:
        """
        Overrides to optimize S3 storage using bulk deletes and
        delegates other storage types to the super() method.
        """
        # 1. HEAVY LIFTING: Clean up S3 storages first using mass deletion
        self._gc_s3_bulk_delete()

        # 2. DELEGATION: Call super() for any remaining storage types
        # Since S3 records have already been removed from fs_file_gc,
        # super() will only process remaining types (Filestore, SFTP, etc.)
        # without hitting timeouts.
        return super()._gc_files_unsafe()

    def _gc_s3_bulk_delete(self):
        """
        Specific logic for S3 using Boto3 Batch.
        Filters storages in memory since autovacuum_gc is not a stored field.
        """
        # Search for all storages and filter by the computed field in Python
        all_storages = self.env["fs.storage"].search([])
        # We filter those with autovacuum active and verify it's an S3-based path
        storages_to_gc = all_storages.filtered(
            lambda s: s.autovacuum_gc and s.is_s3_storage
        )

        for storage in storages_to_gc:
            code = storage.code

            try:
                # directory_path usually contains the bucket name in S3 configurations
                bucket_name = storage.get_directory_path().strip("/")
                root_fs = storage._get_root_filesystem()

                s3_client = root_fs.s3

                if not s3_client or not bucket_name:
                    _logger.warning(
                        "GC: Could not retrieve S3 client or Bucket name for %s", code
                    )
                    continue

                _logger.info(
                    "GC: Starting optimized S3 cleanup for %s in bucket %s",
                    code,
                    bucket_name,
                )

                while fnames := self._list_pending_gc_files(code, self._GC_BATCH_SIZE):
                    # Prepare the keys by removing the protocol prefix (e.g., s3://)
                    objects_to_delete = [{"Key": f.partition("://")[2]} for f in fnames]

                    try:
                        # Perform mass deletion (1 HTTP request per 1000 files)
                        _logger.info(
                            "GC: Sending bulk delete request to S3 (%s files)",
                            len(objects_to_delete),
                        )
                        self.env["fs.storage"]._s3_call_delete_objects(
                            s3_client,
                            Bucket=bucket_name,
                            Delete={"Objects": objects_to_delete},
                        )
                        # Mass delete from database
                        self._cr.execute(
                            "DELETE FROM fs_file_gc WHERE store_fname = ANY(%s)",
                            (fnames,),
                        )

                        # Commit per batch: releases locks and ensures progress is saved
                        self._cr.commit()  # pylint: disable=invalid-commit
                    except Exception as e:
                        _logger.error(
                            "GC Error: Failed S3 delete_objects for %s: %s", code, e
                        )
                        # We break the loop for this storage
                        # to prevent DB deletion if S3 fails
                        break

                    # Explicit memory cleanup
                    gc.collect()

            except Exception as e:
                _logger.error(
                    "GC Error: Could not initialize S3 storage %s: %s", code, e
                )
                continue

        _logger.info("GC: Optimized S3 cleanup process finished.")
