On the Odoo instance, go to *Settings* > *Technical* > *Storage* > *File Storage*.

When you create a new storage for Azure or modify an existing one, when you activate
the option "Use X-Sendfile To Serve Internal Url", 3 additional fields will appear:

- **Azure Uses Signed URL For X-Accel-Redirect**: If checked, the X-Accel-Redirect
  path will be a signed URL, which is useful for Azure storages that require
  signed URLs for access.
- **Azure Signed URL Expiration**: The expiration time for the signed URL in seconds.
  This field is only relevant if the previous option is checked. By default,
  it is set to 30 seconds but it could be less since the url generated into
  the X-Accel-Redirect process is directly used by the web server to serve the file.
- **Azure Delegation Key Expiration**: The lifetime of the user delegation key, in
  seconds. This field is only relevant when the storage authenticates with an
  identity (see below). By default it is set to 1 hour, and Azure does not allow
  more than 7 days.

The value of these fields can also be set in the server environment variables using
the keys:

- *azure_uses_signed_url_for_x_sendfile*
- *azure_signed_url_expiration*
- *azure_delegation_key_expiration*

When the option "Use X-Sendfile To Serve Internal Url" is enabled, the system will
generate an X-Accel-Redirect header in the response to a request to get a file.
In the case of Azure storages, it will follow the format:

```text
X-Accel-Redirect: /fs_x_sendfile/{scheme}/{host}/{path with query if any}
```

Where:

- `{scheme}`: The URL scheme (http or https).
- `{host}`: The host of the Azure storage.
- `{path with query if any}`: The path to the file in the Azure storage,
  including any query parameters. (Query parameters are set when the
  `azure_uses_signed_url_for_x_sendfile` option is enabled.)

In order to serve files using X-Accel-Redirect, you must ensure that your
web server is configured to handle these headers correctly. This typically
involves setting up a location block in your web server configuration that
matches the X-Accel-Redirect path and proxies the request to the Azure storage.

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


Unlike the standard implementation of X-Accel-Redirect on non Azure storages,
the Azure implementation does not require a base URL to be set in the storage
configuration. The X-Accel-Redirect path is constructed directly from the
Azure storage's URL defined for the connection, the directory name as
bucket name, and the file path.

## Signing with an identity

Signed URLs are generated with the account shared key when the storage is configured
with a connection string or an account name/key pair. Otherwise (managed identity,
workload identity, service principal, ...) they are signed with a *user delegation
key*, which requires the identity to have the **Storage Blob Delegator** role on the
storage account, on top of a data plane role such as *Storage Blob Data Reader*.

Delegation keys are obtained from Azure with an extra request, so they are kept in
the cache of the Odoo registry for **Azure Delegation Key Expiration** seconds. They
are requested from Azure for slightly longer than that, so that a key served from the
cache still covers the URLs signed with it.

A higher value means fewer requests to Azure, but also a longer window during which
the key of a revoked identity remains usable. Note that a key already issued by Azure
stays valid until it expires anyway, whatever Odoo does with its copy.

The cache is only kept in memory, so it is never shared between processes nor
persisted in the database, and it is dropped whenever Odoo clears the cache of the
registry, which modifying a storage does. Reconfiguring a storage is therefore
applied right away.
