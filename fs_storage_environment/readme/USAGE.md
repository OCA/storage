To ease the management of the filesystem storages configuration accross
the different environments, the configuration of the filesystem storages
can be defined in environment files or directly in the main
configuration file. For example, the configuration of a filesystem
storage with the code fsprod can be provided in the main configuration
file as follows:

``` ini
[fs_storage.fsprod]
protocol=s3
options={"endpoint_url": "https://my_s3_server/", "key": "KEY", "secret": "SECRET"}
directory_path=my_bucket
```

To work, a storage.backend record must exist with the code fsprod into
the database. In your configuration section, you can specify the value
for the following fields:

- protocol
- options
- directory_path

When evaluating directory_path, {db_name} is replaced by the database
name. This is usefull in multi-tenant with a setup completly controlled
by configuration files.

## Migration from storage_backend

The fs_storage addon can be used to replace the storage_backend addon.
(It has been designed to be a drop-in replacement for the
storage_backend addon). To ease the migration, the fs.storage model
defines the high-level methods available in the storage_backend model.
These methods are:

- add
- get
- list_files
- find_files
- move_files
- delete

These methods are wrappers around the methods of the
fsspec.AbstractFileSystem class (see
<https://filesystem-spec.readthedocs.io/en/latest/api.html#fsspec.spec.AbstractFileSystem>).
These methods are marked as deprecated and will be removed in a future
version (V18) of the addon. You should use the methods of the
fsspec.AbstractFileSystem class instead since they are more flexible and
powerful. You can access the instance of the fsspec.AbstractFileSystem
class using the fs property of a fs.storage record.
