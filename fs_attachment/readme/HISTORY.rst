16.0.1.0.5 (2023-11-29)
~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- When manipulating the file system api through a local variable named *fs*,
  we observed some strange behavior when it was wrongly redefined in an
  enclosing scope as in the following example: *with fs.open(...) as fs*.
  This commit fixes this issue by renaming the local variable and therefore
  avoiding the name clash. (`#306 <https://github.com/OCA/storage/issues/306>`_)


16.0.1.0.4 (2023-11-22)
~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- Fix error when an url is computed for an attachment in a storage configure wihtout directory path. (`#302 <https://github.com/OCA/storage/issues/302>`_)


16.0.1.0.3 (2023-10-17)
~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- Fix access to technical models to be able to upload attachments for users with basic access (`#289 <https://github.com/OCA/storage/issues/289>`_)


16.0.1.0.2 (2023-10-09)
~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- Ensures python 3.9 compatibility. (`#285 <https://github.com/OCA/storage/issues/285>`_)
- If a storage is not used to store all the attachments by default, the call to the
  `get_force_db_for_default_attachment_rules` method must return an empty dictionary. (`#286 <https://github.com/OCA/storage/issues/286>`_)
