In some cases, you need to store attachment in another system that the Odoo's
filestore. For example, when your deployment is based on a multi-server
architecture to ensure redundancy and scalability, your attachments must
be stored in a way that they are accessible from all the servers. In this
way, you can use a shared storage system like NFS or a cloud storage like
S3 compliant storage, or....

This addon extend the storage mechanism of Odoo's attachments to allow
you to store them in any storage filesystem supported by the Python
library `fsspec <https://filesystem-spec.readthedocs.io/en/latest/>`_ and made
available via the `fs_storage` addon.

In contrast to Odoo, when a file is stored into an external storage, this
addon ensures that the filename keeps its meaning (In odoo the filename
into the filestore is the file content checksum). Concretely the filename
is based on the pattern:
'<name-without-extension>-<attachment-id>-<version>.<extension>'
