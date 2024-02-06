Configuration
~~~~~~~~~~~~~

When you create a new backend, you must specify the following:

* The name of the backend. This is the name that will be used to
  identify the backend into Odoo
* The code of the backend. This code will identify the backend into the store_fname
  field of the ir.attachment model. This code must be unique. It will be used
  as scheme. example of the store_fname field: ``odoofs://abs34Tg11``.
* The protocol used by the backend. The protocol refers to the supported
  protocols of the fsspec python package.
* A directory path. This is a root directory from which the filesystem will
  be mounted. This directory must exist.
* The protocol options. These are the options that will be passed to the
  fsspec python package when creating the filesystem. These options depend
  on the protocol used and are described in the fsspec documentation.
* Resolve env vars. This options resolves the protocol options values starting
  with $ from environment variables

Some protocols defined in the fsspec package are wrappers around other
protocols. For example, the SimpleCacheFileSystem protocol is a wrapper
around any local filesystem protocol. In such cases, you must specify into the
protocol options the protocol to be wrapped and the options to be passed to
the wrapped protocol.

For example, if you want to create a backend that uses the SimpleCacheFileSystem
protocol, after selecting the SimpleCacheFileSystem protocol, you must specify
the protocol options as follows:

.. code-block:: python

    {
        "directory_path": "/tmp/my_backend",
        "target_protocol": "odoofs",
        "target_options": {...},
    }

In this example, the SimpleCacheFileSystem protocol will be used as a wrapper
around the odoofs protocol.

Server Environment
~~~~~~~~~~~~~~~~~~

To ease the management of the filesystem storages configuration accross the different
environments, the configuration of the filesystem storages can be defined in
environment files or directly in the main configuration file. For example, the
configuration of a filesystem storage with the code `fsprod` can be provided in the
main configuration file as follows:

.. code-block:: ini

  [fs_storage.fsprod]
  protocol=s3
  options={"endpoint_url": "https://my_s3_server/", "key": "KEY", "secret": "SECRET"}
  directory_path=my_bucket

To work, a `storage.backend` record must exist with the code `fsprod` into the database.
In your configuration section, you can specify the value for the following fields:

* `protocol`
* `options`
* `directory_path`

Migration from storage_backend
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The fs_storage addon can be used to replace the storage_backend addon. (It has
been designed to be a drop-in replacement for the storage_backend addon). To
ease the migration, the `fs.storage` model defines the high-level methods
available in the storage_backend model. These methods are:

* `add`
* `get`
* `list_files`
* `find_files`
* `move_files`
* `delete`

These methods are wrappers around the methods of the `fsspec.AbstractFileSystem`
class (see https://filesystem-spec.readthedocs.io/en/latest/api.html#fsspec.spec.AbstractFileSystem).
These methods are marked as deprecated and will be removed in a future version (V18)
of the addon. You should use the methods of the `fsspec.AbstractFileSystem` class
instead since they are more flexible and powerful. You can access the instance
of the `fsspec.AbstractFileSystem` class using the `fs` property of a `fs.storage`
record.
