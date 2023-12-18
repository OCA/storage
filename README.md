
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/storage&target_branch=12.0)
[![Pre-commit Status](https://github.com/OCA/storage/actions/workflows/pre-commit.yml/badge.svg?branch=12.0)](https://github.com/OCA/storage/actions/workflows/pre-commit.yml?query=branch%3A12.0)
[![Build Status](https://github.com/OCA/storage/actions/workflows/test.yml/badge.svg?branch=12.0)](https://github.com/OCA/storage/actions/workflows/test.yml?query=branch%3A12.0)
[![codecov](https://codecov.io/gh/OCA/storage/branch/12.0/graph/badge.svg)](https://codecov.io/gh/OCA/storage)
[![Translation Status](https://translation.odoo-community.org/widgets/storage-12-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/storage-12-0/?utm_source=widget)

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
[storage_backend](storage_backend/) | 12.0.2.0.4 |  | Implement the concept of Storage with amazon S3, sftp...
[storage_backend_s3](storage_backend_s3/) | 12.0.2.1.1 |  | Implement amazon S3 Storage
[storage_backend_sftp](storage_backend_sftp/) | 12.0.2.0.0 |  | Implement SFTP Storage
[storage_file](storage_file/) | 12.0.2.0.4 |  | Storage file in storage backend
[storage_image](storage_image/) | 12.0.2.4.2 |  | Store image and resized image in a storage backend
[storage_image_product](storage_image_product/) | 12.0.1.2.2 |  | Link images to products and categories
[storage_thumbnail](storage_thumbnail/) | 12.0.2.0.2 |  | Abstract module that add the possibility to have thumbnail


Unported addons
---------------
addon | version | maintainers | summary
--- | --- | --- | ---
[storage_image_category_pos](storage_image_category_pos/) | 10.0.1.0.0 (unported) |  | Add image handling to product category and use it for POS
[storage_image_product_pos](storage_image_product_pos/) | 10.0.1.0.0 (unported) |  | Link images to products and categories inside POS
[storage_media](storage_media/) | 10.0.1.0.0 (unported) |  | Give the posibility to store media data in Odoo
[storage_media_product](storage_media_product/) | 10.0.2.0.0 (unported) |  | Link media to products and categories

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to Odoo Community Association (OCA)
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----
OCA, or the [Odoo Community Association](http://odoo-community.org/), is a nonprofit
organization whose mission is to support the collaborative development of Odoo features
and promote its widespread use.
