
.. image:: https://img.shields.io/badge/licence-LGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
   :alt: License: LGPL-3

===================
Storage backend S3
===================

Add the possibility to store and get data from amazon S3 for your storage backend



Installation
============

To install this module, you need to:

#. (root) pip install boto


Known issues / Roadmap
======================

Update README with the last model of README when migration to v11 in OCA

There is an issue with the latest version of `boto3` and `urllib3`
- boto3 needs to be `boto3<=1.15.17` related with https://github.com/OCA/storage/issues/67


Credits
=======


Contributors
------------

* Sebastien Beau <sebastien.beau@akretion.com>
* Raphaël Reverdy <raphael.reverdy@akretion.com>


Maintainer
----------

* Akretion
