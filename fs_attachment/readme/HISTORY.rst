16.0.3.1.0 (2026-06-24)
~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- Paginate the autovacuum GC loop to bound worker memory.

  ``FsFileGC._gc_files_unsafe`` used to load the entire backlog of orphan
  files into a single Python list via ``array_agg(store_fname)`` and iterate
  ``fs.rm`` over all of them in one pass. With the Azure Blob backend and
  tens of thousands of orphans queued, each HEAD+DELETE pair retained
  response buffers and connection-pool state inside the adlfs client that
  was only released when the worker exited. The autovacuum cron hit Odoo's
  ``limit_memory_hard`` and got ``SIGKILL``'d mid-run every time, so the
  queue never drained and the next worker ran the same failing loop.

  The SELECT and the ``fs.rm`` loop are now paginated in batches of 500 per
  storage, with an explicit ``gc.collect()`` between batches. The caller
  (``_gc_files``) still holds the ``SHARE`` lock and performs the final
  commit, so the consistency guarantees and transactional semantics are
  unchanged. (`#gc_batching <https://github.com/OCA/storage/issues/gc_batching>`_)


16.0.2.1.0 (2026-05-26)
~~~~~~~~~~~~~~~~~~~~~~~

**Features**

- Adapt to handle {db_name} in directory_path. (`#db_name <https://github.com/OCA/storage/issues/db_name>`_)


16.0.2.0.3 (2026-05-26)
~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- Bound the GC cursor with per-transaction timeouts.

  The secondary cursor opened by ``FsFileGC._in_new_cursor`` had no upper
  bound, so a slow or unresponsive external storage backend (observed on
  Azure Blob, same class of issue applies to S3) could leave it
  ``idle in transaction`` while waiting on network I/O. The cursor kept a
  row lock on ``fs_file_gc`` (via the ``store_fname`` unique constraint in
  ``_mark_for_gc``), serialising every concurrent attachment write until
  the Odoo session ``statement_timeout`` killed it — by which time every
  ``POST /mail/attachment/upload`` was returning a 500 HTML page, which
  the frontend tried to ``JSON.parse`` and failed with
  ``Unexpected token '<', "<!DOCTYPE"...``. A ``SET LOCAL statement_timeout``
  and ``SET LOCAL idle_in_transaction_session_timeout`` on the new cursor
  cap the damage to 30-60 s and let the main transaction fail fast instead
  of stalling the whole instance. (`#gc_cursor_timeout <https://github.com/OCA/storage/issues/gc_cursor_timeout>`_)


16.0.1.0.13 (2024-05-10)
~~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- No crash o missign file.

  Prior to this change, Odoo was crashing as soon as access to a file stored into
  an external filesytem was not possible. This can lead to a complete system block.
  This change prevents this kind of blockage by ignoring access error to files
  stored into external system on read operations. These kind of errors are logged
  into the log files for traceability. (`#361 <https://github.com/OCA/storage/issues/361>`_)


16.0.1.0.8 (2023-12-20)
~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- Fix the error retrieving attachment files when the storage is set to optimize directory paths. (`#312 <https://github.com/OCA/storage/issues/312>`_)


16.0.1.0.6 (2023-12-02)
~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- Improve performance at creation of an attachment or when the attachment is updated.

  Before this change, when the fs_url was computed the computed value was always
  reassigned to the fs_url attribute even if the value was the same. In a lot of
  cases the value was the same and the reassignment was not necessary. Unfortunately
  this reassignment has as side effect to mark the record as dirty and generate a
  SQL update statement at the end of the transaction. (`#307 <https://github.com/OCA/storage/issues/307>`_)


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
