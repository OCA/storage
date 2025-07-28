On the Odoo instance, go to *Settings* > *Technical* > *Storage* > *File Storage*.

When you create a new storage for s3 or modify an existing one, when you activate
the option "Use X-Sendfile To Serve Internal Url", 2 additional fields will appear:
- **S3 Uses Signed URL For X-Accel-Redirect**: If checked, the X-Accel-Redirect
  path will be a signed URL, which is useful for S3 storages that require
  signed URLs for access.
- **S3 Signed URL Expiration**: The expiration time for the signed URL in seconds.
  This field is only relevant if the previous option is checked. By default,
  it is set to 60 seconds but it could be less since the url generated into
  the X-Accel-Redirect process is directly used by the web server to serve the file.

The value of these fields can also be set in the server environment variables using
the keys:
- *s3_uses_signed_url_for_x_accel_redirect*
- *s3_signed_url_expiration*

To work properly, you must also configure your web server to handle
X-Accel-Redirect or X-Sendfile headers. You can find more information
about this in the documentation of the [fs_attachment](https://github.com/OCA/storage/tree/16.0/fs_attachment) module.

In the case of a S3 storage, the base URL and base URL for X-Sendfile
field on the storage configuration are not mandatory. If not set,
the storage will use the S3 bucket URL as the base URL for X-Accel-Redirect.