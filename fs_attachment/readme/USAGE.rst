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

Another key feature of this module is the ability to get access to the attachments
from URLs.

* ``Base URL``: This is the base URL used to access the attachments from the
  filesystem storage itself.
* ``Is Directory Path In URL``: Normally the directory patch configured on the storage
  is not included in the URL. If you want to include it, you can activate this option.

Tips & Tricks
~~~~~~~~~~~~~

* When working in multi staging environments, the management of the attachments
  can be tricky. For example, if you have a production instance and a staging
  instance based on a backup of the production environment, you may want to have
  the attachments shared between the two instances BUT you don't want to have
  one instance removing or modifying the attachments of the other instance.

  To do so, you can configure the same filesystem storage on both instances and
  use a different directory path. (For S3 storage, directory path is the bucket
  name). When a file is written in the filesystem storage, it's always written into
  the directory path configured on the storage and full path of the file is stored
  in the database. When reading a file, it's always read from the full path stored
  in the database. So if you have two instances using the same storage with different
  directory paths, files written in each instance will be stored in different
  directories but be accessible from the other instance. A check is also done when
  an attachment is removed to ensure that only files stored in the current directory
  path are removed.
