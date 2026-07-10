This module extends the functionality of [fs_attachment](https://github.com/OCA/storage/tree/16.0/fs_attachment) 
to better support Amazon S3 storage. It includes features such as:

- Special handling of X-Accel-Redirect headers for S3 storages.
- Options for using signed URLs in X-Accel-Redirect. (This is required to be able to serve files from a private S3 bucket 
  using X-Accel-Redirect without exposing the files publicly.)
- Enforcing the mimetype of files stored in S3.
