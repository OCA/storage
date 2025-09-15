On the Odoo instance, go to *Settings* > *Technical* > *Storage* > *File Storage*.

When you create a new storage for s3 or modify an existing one, when you activate
the option "Use X-Sendfile To Serve Internal Url", 2 additional fields will appear:

- **S3 Uses Signed URL For X-Accel-Redirect**: If checked, the X-Accel-Redirect
  path will be a signed URL, which is useful for S3 storages that require
  signed URLs for access.
- **S3 Signed URL Expiration**: The expiration time for the signed URL in seconds.
  This field is only relevant if the previous option is checked. By default,
  it is set to 30 seconds but it could be less since the url generated into
  the X-Accel-Redirect process is directly used by the web server to serve the file.

The value of these fields can also be set in the server environment variables using
the keys:

- *s3_uses_signed_url_for_x_sendfile*
- *s3_signed_url_expiration*

When the option "Use X-Sendfile To Serve Internal Url" is enabled, the system will
generate an X-Accel-Redirect header in the response to a request to get a file.
In the case of S3 storages, it will follow the format:

```text
X-Accel-Redirect: /fs_x_sendfile/{scheme}/{host}/{path with query if any}
```

Where:

- `{scheme}`: The URL scheme (http or https).
- `{host}`: The host of the S3 storage.
- `{path with query if any}`: The path to the file in the S3 storage,
  including any query parameters. (Query parameters are set when the
  `s3_uses_signed_url_for_x_sendfile` option is enabled.)

In order to serve files using X-Accel-Redirect, you must ensure that your
web server is configured to handle these headers correctly. This typically
involves setting up a location block in your web server configuration that
matches the X-Accel-Redirect path and proxies the request to the S3 storage.

For example, if you are using Nginx, you would add a location block like this:

```nginx

    location ~ ^/fs_x_sendfile/(.*?)/(.*?)/(.*) {
        internal;
        set $url_scheme $1;
        set $url_host $2;
        set $url_path $3;
        set $url $url_scheme://$url_host/$url_path;

        proxy_pass $url$is_args$args;
        proxy_set_header Host $url_host;
        proxy_ssl_server_name on;
     
    }
```


Unlike the standard implementation of X-Accel-Redirect on non S3 storages,
the S3 implementation does not require a base URL to be set in the storage
configuration. The X-Accel-Redirect path is constructed directly from the
S3 storage's URL defined for the connection, the directory name as
bucket name, and the file path.
