Configuration
~~~~~~~~~~~~~

The configuration is done through the creation of a filesytem storage record
into odoo. To create a new storage, go to the menu
``Settings > Technical > FS Storage`` and click on ``Create``.

In addition to the common fields available to configure a storage, specifics
fields are available under the section 'Attachment' to configure the way
attachments will be stored in the filesystem.

* ``Optimizes Directory Path``: This option is useful if you need to prevent
  having too many files in a single directory. It will create a directory
  structure based on the attachment's checksum (with 2 levels of depth)
  For example, if the checksum is ``123456789``, the file will be stored in the
  directory  ``/path/to/storage/12/34/my_file-1-0.txt``.
* ``Autovacuum GC``: This is used to automatically remove files from the filesystem
  when it's no longer referenced in Odoo. Some storage backends (like S3) may
  charge you for the storage of files, so it's important to remove them when
  they're no longer needed. In some cases, this option is not desirable, for
  example if you're using a storage backend to store images shared with others
  systems (like your website) and you don't want to remove the files from the
  storage while they're still referenced into the others systems.
  This mechanism is based on a ``fs.file.gc`` model used to collect the files
  to remove. This model is automatically populated by the ``ir.attachment``
  model when a file is removed from the database. If you disable this option,
  you'll have to manually take care of the records in the ``fs.file.gc`` for
  your filesystem storage.
* ``Use As Default For Attachment``: This options allows you to declare the storage
  as the default one for attachments. If you have multiple filesystem storage
  configured, you can choose which one will be used by default for attachments.
  Once activated, attachments created without specifying a storage will be
  stored in this default storage.
* ``Force DB For Default Attachment Rules``: This option is useful if you want to
  force the storage of some attachments in the database, even if you have a
  default filesystem storage configured. This is specially useful when you're
  using a storage backend like S3, where the latency of the network can be
  high. This option is a JSON field that allows you to define the mimetypes and
  the size limit below which the attachments will be stored in the database.

  Small images (128, 256) are used in Odoo in list / kanban views. We
  want them to be fast to read.
  They are generally < 50KB (default configuration) so they don't take
  that much space in database, but they'll be read much faster than from
  the object storage.

  The assets (application/javascript, text/css) are stored in database
  as well whatever their size is:

  * a database doesn't have thousands of them
  * of course better for performance
  * better portability of a database: when replicating a production
    instance for dev, the assets are included

  The default configuration is:

   {"image/": 51200, "application/javascript": 0, "text/css": 0}

   Where the key is the beginning of the mimetype to configure and the
   value is the limit in size below which attachments are kept in DB.
   0 means no limit.

  Default configuration means:

  * images mimetypes (image/png, image/jpeg, ...) below 50KB are
    stored in database
  * application/javascript are stored in database whatever their size
  * text/css are stored in database whatever their size

  This option is only available on the filesystem storage that is used
  as default for attachments.

It is also possible to use different FS storages for attachments linked to
different resource fields/models. You can configure it either on the ``fs.storage``
directly, or in a server environment file:

* From the ``fs.storage``: Fields `model_ids` and `field_ids` will encode for which
  models/fields use this storage as default storage for attachments having these resource
  model/field. Note that if an attachment has both resource model and field, it will
  first take the FS storage where the field is explicitely linked, then is not found,
  the one where the model is explicitely linked.

* From a server environment file: In this case you just have to provide a comma-
  separated list of models (under the `model_xmlids` key) or fields (under the
  `field_xmlids` key). To do so, use the model/field XML ids provided by Odoo.
  See the Server Environment section for a concrete example.

Another key feature of this module is the ability to get access to the attachments
from URLs.

* ``Base URL``: This is the base URL used to access the attachments from the
  filesystem storage itself. If your storage doesn't provide a way to access
  the files from a URL, you can leave this field empty.
* ``Is Directory Path In URL``: Normally the directory patch configured on the storage
  is not included in the URL. If you want to include it, you can activate this option.
* ``Use X-Sendfile To Serve Internal Url``: If checked and odoo is behind a proxy
  that supports x-sendfile, the content will be served by the proxy. This means
  that the charge on the odoo process will be reduced and the files will be served
  directly by the proxy. In order to use this option, you must also a ``base URL``
  or a ``Base URL for X-Sendfile``. This URL will be used to serve the files
  through the proxy. The concatenation of this URL with the file path
  will give the URL to access the file. For example, if the base URL is
  ``https://my.public.files/`` and the file path is ``/my_picture.png``, the
  URL to access the file will be ``https://my.public.files/my_picture.png``.

  To be fully functional, this option requires the proxy to support x-sendfile
  (apache) or x-accel-redirect (nginx). You must also configure your proxy by
  adding for each storage a rule to redirect the url rooted at the 'storagge code'
  to the server serving the files. For example, if you have a storage with the
  code 'my_storage' and a server serving the files at the url 'http://myserver.com',
  you must add the following rule in your proxy configuration:

  .. code-block:: nginx

    location ~ ^/fs_x_accel_redirect/(.*?)/(.*?)/(.*) {
        internal;
        set $url_protocol $1;
        set $url_host $2;
        set $url_path $3;
        set $url $url_protocol://$url_host/$url_path;

        proxy_pass $url$is_args$args;
        proxy_set_header Host $url_host;
        proxy_ssl_server_name on;
     
        # Optional: Forward original filename (if needed)
        proxy_set_header X-Original-URI $request_uri;
    }

  When Odoo builds the respone to serve the attachment, it will
  add the headers ``X-Accel-Redirect`` and ``X-Sendfile`` with the URL to access
  the file. By convention, the URL will be in the format
  ``/fs_x_accel_redirect/<protocol>/<host>/<path>`` where `<protocol>` is the protocol
  used to access the file (http or https), `<host>` is the host of the
  server serving the files and `<path>` is the path to the file on the server.

  For example, if the base URL is ``https://my.public.files/`` and the file path
  is ``/my_picture.png``, the URL to access the file will be
  ``/fs_x_accel_redirect/https/my.public.files/my_picture.png``.

  This rule is generic and will work for any storage configured with the
  `Use X-Sendfile To Serve Internal Url` option. The proxy will then redirect
  the request to the server serving the files.

* ``Base URL for X-Sendfile``: This is the base URL used to access the attachments
  when the `Use X-Sendfile To Serve Internal Url` option is activated. If not set,
  the base URL of the storage will be used. The motivation for this field
  is to allow the use of specific URL for accessing the files through
  the proxy than the base URL of the storage itself. (For example, your base URL
  could be a CDN URL, but you want to access the files through a specific private URL)

* ``Use Filename Obfuscation``: If checked, the filename used to store the content
  into the filesystem storage will be obfuscated. This is useful to avoid to
  expose the real filename of the attachments outside of the Odoo database.
  The filename will be obfuscated by using the checksum of the content. This option
  is to avoid when the content of your filestore is shared with other systems
  (like your website) and you want to keep a meaningful filename to ensure
  SEO. This option is disabled by default.


Server Environment
~~~~~~~~~~~~~~~~~~

When you configure a storage through the use of server environment file, you can
provide values for the following keys:

* ``optimizes_directory_path``
* ``autovacuum_gc``
* ``base_url``
* ``is_directory_path_in_url``
* ``use_x_sendfile_to_serve_internal_url``
* ``use_as_default_for_attachments``
* ``force_db_for_default_attachment_rules``
* ``use_filename_obfuscation``
* ``model_xmlids``
* ``field_xmlids``

For example, the configuration of my storage with code `fsprod` used to store
the attachments by default could be:

.. code-block:: ini

    [fs_storage.fsprod]
    protocol=s3
    options={"endpoint_url": "https://my_s3_server/", "key": "KEY", "secret": "SECRET"}
    directory_path=my_bucket
    use_as_default_for_attachments=True
    use_filename_obfuscation=True
    model_xmlids=base.model_res_lang,base.model_res_country
    field_xmlids=base.field_res_partner__image_128

Advanced usage: Using attachment as a file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The `open` method on the attachment can be used to open manipulate the attachment
as a file object. The object returned by the call to the method implements
methods from ``io.IOBase``.  The method can ba called as any other python method.
In such a case, it's your responsibility to close the file at the end of your
process.

.. code-block:: python

    attachment = self.env.create({"name": "test.txt"})
    the_file = attachment.open("wb")
    try:
      the_file.write(b"content")
    finally:
      the_file.close()

The result of the call to `open` also works in a context ``with`` block. In such
a case, when the code exit the block, the file is automatically closed.

.. code-block:: python

    attachment = self.env.create({"name": "test.txt"})
    with attachment.open("wb") as the_file:
      the_file.write(b"content")

It's always safer to prefer the second approach.

When your attachment is stored into the odoo filestore or into an external
filesystem storage, each time you call the open method, a new file is created.
This way of doing ensures that if the transaction is rolled back the original content
is preserved. Nevertheless you could have use cases where you would like to write
to the existing file directly. For example you could create an empty attachment
to store a csv report and then use the `open` method to write your content directly
into the new file. To support this kind a use cases, the parameter `new_version`
can be passed as `False` to avoid the creation of a new file.

.. code-block:: python

    attachment = self.env.create({"name": "test.txt"})
    with attachment.open("w", new_version=False) as f:
        writer = csv.writer(f, delimiter=";")
        ....


Tips & Tricks
~~~~~~~~~~~~~

* When working in multi staging environments, the management of the attachments
  can be tricky. For example, if you have a production instance and a staging
  instance based on a backup of the production environment, you may want to have
  the attachments shared between the two instances BUT you don't want to have
  one instance removing or modifying the attachments of the other instance.

  To do so, you can add on your staging instances a new storage and declare it
  as the default storage to use for attachments. This way, all the new attachments
  will be stored in this new storage but the attachments created on the production
  instance will still be read from the production storage. Be careful to adapt the
  configuration of your storage to the production environment to make it read only.
  (The use of server environment files is a good way to do so).
