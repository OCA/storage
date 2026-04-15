
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/storage&target_branch=19.0)
[![Pre-commit Status](https://github.com/OCA/storage/actions/workflows/pre-commit.yml/badge.svg?branch=19.0)](https://github.com/OCA/storage/actions/workflows/pre-commit.yml?query=branch%3A19.0)
[![Build Status](https://github.com/OCA/storage/actions/workflows/test.yml/badge.svg?branch=19.0)](https://github.com/OCA/storage/actions/workflows/test.yml?query=branch%3A19.0)
[![codecov](https://codecov.io/gh/OCA/storage/branch/19.0/graph/badge.svg)](https://codecov.io/gh/OCA/storage)
[![Translation Status](https://translation.odoo-community.org/widgets/storage-19-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/storage-19-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# storage

storage

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[fs_attachment](fs_attachment/) | 19.0.1.1.1 | <a href='https://github.com/lmignon'><img src='https://github.com/lmignon.png' width='32' height='32' style='border-radius:50%;' alt='lmignon'/></a> | Store attachments on external object store
[fs_attachment_s3](fs_attachment_s3/) | 19.0.1.2.0 | <a href='https://github.com/lmignon'><img src='https://github.com/lmignon.png' width='32' height='32' style='border-radius:50%;' alt='lmignon'/></a> | Store attachments into S3 complient filesystem
[fs_storage](fs_storage/) | 19.0.1.1.2 |  | Implement the concept of Storage with amazon S3, sftp...


Unported addons
---------------
addon | version | maintainers | summary
--- | --- | --- | ---
[fs_file](fs_file/) | 18.0.1.0.0 (unported) | <a href='https://github.com/lmignon'><img src='https://github.com/lmignon.png' width='32' height='32' style='border-radius:50%;' alt='lmignon'/></a> | Field to store files into filesystem storages
[fs_folder](fs_folder/) | 18.0.2.0.0 (unported) | <a href='https://github.com/lmignon'><img src='https://github.com/lmignon.png' width='32' height='32' style='border-radius:50%;' alt='lmignon'/></a> | A module to link to Odoo records and manage from record forms forlders from external file systems
[fs_folder_demo](fs_folder_demo/) | 18.0.1.0.0 (unported) |  | Demo for fs_folder addon
[fs_folder_ms_drive](fs_folder_ms_drive/) | 18.0.2.0.0 (unported) | <a href='https://github.com/lmignon'><img src='https://github.com/lmignon.png' width='32' height='32' style='border-radius:50%;' alt='lmignon'/></a> | Display and manage your files from Microsoft drives from within Odoo
[fs_folder_webdav](fs_folder_webdav/) | 18.0.1.0.0 (unported) | <a href='https://github.com/jguenat'><img src='https://github.com/jguenat.png' width='32' height='32' style='border-radius:50%;' alt='jguenat'/></a> | UI improvement when managing WebDAV folder
[fs_image](fs_image/) | 18.0.1.0.0 (unported) | <a href='https://github.com/lmignon'><img src='https://github.com/lmignon.png' width='32' height='32' style='border-radius:50%;' alt='lmignon'/></a> | Field to store images into filesystem storages
[fs_storage_ms_drive](fs_storage_ms_drive/) | 18.0.2.0.0 (unported) | <a href='https://github.com/lmignon'><img src='https://github.com/lmignon.png' width='32' height='32' style='border-radius:50%;' alt='lmignon'/></a> | Add the microsoft drives (OneDrive, Sharepoint) as a storage backend
[image_tag](image_tag/) | 18.0.1.0.0 (unported) |  | Image tag model
[microsoft_drive_account](microsoft_drive_account/) | 18.0.2.0.0 (unported) | <a href='https://github.com/lmignon'><img src='https://github.com/lmignon.png' width='32' height='32' style='border-radius:50%;' alt='lmignon'/></a> | Link user with Microsoft
[storage_backend](storage_backend/) | 18.0.1.0.0 (unported) |  | Implement the concept of Storage with amazon S3, sftp...
[storage_backend_ftp](storage_backend_ftp/) | 18.0.1.0.0 (unported) |  | Implement FTP Storage
[storage_backend_s3](storage_backend_s3/) | 18.0.1.1.0 (unported) |  | Implement amazon S3 Storage
[storage_backend_sftp](storage_backend_sftp/) | 18.0.1.0.0 (unported) |  | Implement SFTP Storage
[storage_file](storage_file/) | 18.0.1.0.0 (unported) |  | Storage file in storage backend
[storage_image](storage_image/) | 18.0.1.0.1 (unported) |  | Store image and resized image in a storage backend
[storage_image_product](storage_image_product/) | 18.0.1.0.1 (unported) |  | Link images to products and categories
[storage_media](storage_media/) | 18.0.1.1.1 (unported) |  | Give the posibility to store media data in Odoo
[storage_media_product](storage_media_product/) | 18.0.1.0.1 (unported) |  | Link media to products and categories
[storage_thumbnail](storage_thumbnail/) | 18.0.1.0.0 (unported) |  | Abstract module that add the possibility to have thumbnail

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
