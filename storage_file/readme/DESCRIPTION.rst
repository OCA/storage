External file management depending on Storage Backend module.

It include these features:
* link to any Odoo model/record
* store metadata like: checksum, mimetype

Use cases (with help of additional modules):
- store pdf (like invoices) on a file server with high SLA
- access attachments with read/write on prod environment and only read only on dev / testing
