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
* Check Connection Method. If set, Odoo will always check the connection before using
  a storage and it will remove the fs connection from the cache if the check fails.

  * ``Create Marker file`` : create a hidden file on remote and then check it exists with
    Use it if you have write access to the remote and if it is not an issue to leave
    the marker file in the root directory.
  * ``List file`` : list all files from the root directory. You can use it if the directory
    path does not contain a big list of files (for performance reasons)

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
