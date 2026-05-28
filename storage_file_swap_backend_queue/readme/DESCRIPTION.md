This module integrates `storage_file` with `queue_job` to delegate the
backend swap operation to asynchronous jobs.

When swapping files between storage backends via the wizard, the
operation is split into batches and dispatched as queue jobs instead of
running synchronously. This avoids timeouts when moving large numbers of
files.
