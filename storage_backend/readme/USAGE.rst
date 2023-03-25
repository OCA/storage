When you create a new backend, you must specify the following:

* The name of the backend. This is the name that will be used to
  identify the backend into Odoo
* The protocol used by the backend. The protocol refers to the supported
  protocols of the fsspec python package.
* A directory path. This is a root directory from which the filesystem will
  be mounted. This directory must exist.
* The protocol options. These are the options that will be passed to the
  fsspec python package when creating the filesystem. These options depend
  on the protocol used and are described in the fsspec documentation.

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
