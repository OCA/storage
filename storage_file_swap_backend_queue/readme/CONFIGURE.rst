The batch size (number of files processed per job) can be tuned via the
system parameter:

``storage_file_swap_backend_queue.swap_backend_batch_size``

Default value is **5**. Set it in *Settings > Technical > Parameters >
System Parameters* to adjust throughput vs. job granularity.

A dedicated job channel ``root.storage_file_swap`` is created at install.
You can configure its concurrency in *Settings > Technical > Queue Job >
Channels*.
