This module lets users move existing `ir.attachment` files from the
standard filestore or database into an Amazon S3-backed `fs.storage`, using a
 wizard directly on the storage form.

Migrations run in background batches, skip attachments that already live on S3 or must remain in
PostgreSQL, so the process can be launched repeatedly without duplicates.

