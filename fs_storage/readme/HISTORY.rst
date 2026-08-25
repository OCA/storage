16.0.2.0.1 (2026-08-25)
~~~~~~~~~~~~~~~~~~~~~~~

**Features**

- - Remove the dependancy of server_environment module and make fs_storage_environment a bridge between fs_storage and server_environment modules. (`#627 <https://github.com/OCA/storage/issues/627>`_)


16.0.1.5.0 (2026-05-26)
~~~~~~~~~~~~~~~~~~~~~~~

**Features**

- Replace {db_name} by the database name in directory_path (`#db_name <https://github.com/OCA/storage/issues/db_name>`_)


16.0.1.2.0 (2024-02-06)
~~~~~~~~~~~~~~~~~~~~~~~

**Features**

- Invalidate FS filesystem object cache when the connection fails, forcing a reconnection. (`#320 <https://github.com/OCA/storage/issues/320>`_)


16.0.1.1.0 (2023-12-22)
~~~~~~~~~~~~~~~~~~~~~~~

**Features**

- Add parameter on storage backend to resolve protocol options values starting with $ from environment variables (`#303 <https://github.com/OCA/storage/issues/303>`_)


16.0.1.0.3 (2023-10-17)
~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- Fix access to technical models to be able to upload attachments for users with basic access (`#289 <https://github.com/OCA/storage/issues/289>`_)


16.0.1.0.2 (2023-10-09)
~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- Avoid config error when using the webdav protocol. The auth option is expected
  to be a tuple not a list. Since our config is loaded from a json file, we
  cannot use tuples. The fix converts the list to a tuple when the config is
  related to a webdav protocol and the auth option is into the confix. (`#285 <https://github.com/OCA/storage/issues/285>`_)
