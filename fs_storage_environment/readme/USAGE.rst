Configuration
~~~~~~~~~~~~~

When you create a new backend, you must specify the following:

* Resolve env vars. This options resolves the protocol options values starting
  with $ from environment variables

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
