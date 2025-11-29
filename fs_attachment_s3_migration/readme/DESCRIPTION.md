This module lets users move existing `ir.attachment` files from the
standard filestore or database into an Amazon S3-backed `fs.storage`, using a
wizard directly on the storage form.

Migrations are run in background batches, skipping attachments that are already
stored in S3 or must remain in PostgreSQL. This allows to run the process
repeatedly avoiding creating duplicates.

