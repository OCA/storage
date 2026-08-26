This module lets users move existing `ir.attachment` files from the
standard Odoo filestore into an Amazon S3-backed `fs.storage`, using a
wizard on the storage form.

Attachments stored in the database (`db_datas`) are **not** migrated: they
stay in PostgreSQL. They may still be used as a data source when another
attachment with the same checksum is migrated and the original filestore
file is missing.

Migrations run in background batches, skipping attachments that are already
stored on the target S3 storage or that must remain in PostgreSQL according
to the storage's force-DB rules. The process is idempotent and can be run
repeatedly. Original local filestore files are not deleted; disk cleanup is
handled outside this module.
