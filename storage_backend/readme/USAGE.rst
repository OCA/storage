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
