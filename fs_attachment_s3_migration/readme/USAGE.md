1. Open the target S3 `fs.storage` record and click *Move existing attachments
   to S3* in the header.
2. In the migration wizard, keep or adjust the batch size, queue channel, and
   optional *Max Batches* value, then confirm to enqueue jobs. The target
   storage code is taken from the selected `fs.storage` record and cannot be
   overridden independently.
3. The migration **copies** blobs to S3 and repoints `store_fname`. The original
   local filestore files are **not** deleted by this module.
