
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/storage&target_branch=13.0)
[![Build Status](https://travis-ci.com/OCA/storage.svg?branch=13.0)](https://travis-ci.com/OCA/storage)
[![codecov](https://codecov.io/gh/OCA/storage/branch/13.0/graph/badge.svg)](https://codecov.io/gh/OCA/storage)
[![Translation Status](https://translation.odoo-community.org/widgets/storage-13-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/storage-13-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# Storage

External storage integration for Odoo

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[storage_backend](storage_backend/) | 13.0.1.4.1 |  | Implement the concept of Storage with amazon S3, sftp...
[storage_backend_ftp](storage_backend_ftp/) | 13.0.1.1.0 |  | Implement FTP Storage
[storage_backend_s3](storage_backend_s3/) | 13.0.1.2.0 |  | Implement amazon S3 Storage
[storage_backend_sftp](storage_backend_sftp/) | 13.0.1.4.1 |  | Implement SFTP Storage
[storage_file](storage_file/) | 13.0.1.5.1 |  | Storage file in storage backend
[storage_image](storage_image/) | 13.0.1.5.1 |  | Store image and resized image in a storage backend
[storage_image_backend_migration](storage_image_backend_migration/) | 13.0.1.0.0 |  | Migrate src backend to destination backend
[storage_image_product](storage_image_product/) | 13.0.3.0.1 |  | Link images to products and categories
[storage_image_product_brand](storage_image_product_brand/) | 13.0.1.1.0 |  | Link images to product brands
[storage_import_image_advanced](storage_import_image_advanced/) | 13.0.1.0.3 |  | Import product images using CSV
[storage_media](storage_media/) | 13.0.1.2.0 |  | Give the posibility to store media data in Odoo
[storage_media_product](storage_media_product/) | 13.0.1.2.1 |  | Link media to products and categories
[storage_thumbnail](storage_thumbnail/) | 13.0.1.3.0 |  | Abstract module that add the possibility to have thumbnail


Unported addons
---------------
addon | version | maintainers | summary
--- | --- | --- | ---
[storage_image_category_pos](storage_image_category_pos/) | 10.0.1.0.0 (unported) |  | Add image handling to product category and use it for POS
[storage_image_product_pos](storage_image_product_pos/) | 10.0.1.0.0 (unported) |  | Link images to products and categories inside POS

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [LGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to Odoo Community Association (OCA)
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----
OCA, or the [Odoo Community Association](http://odoo-community.org/), is a nonprofit
organization whose mission is to support the collaborative development of Odoo features
and promote its widespread use.
