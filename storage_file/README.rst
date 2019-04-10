
.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

============
Storage File
============


External file management depending on Storage Backend module.

It include these features:
* link to any Odoo model/record
* store metadata like: checksum, mimetype

Use cases (with help of additionnal modules):
- store pdf (like invoices) on a file server with high SLA
- access attachments with read/write on prod environment and only read only on dev / testing

Known issues / Roadmap
======================

* Update README with the last model of README when migration to v11 in OCA
* No file deletion / unlink

Credits
=======


Contributors
------------

* Sebastien Beau <sebastien.beau@akretion.com>
* Raphaël Reverdy <raphael.reverdy@akretion.com>


Maintainer
----------

* Akretion
