This module defines a reusable storage backend model for Odoo.

It serves as a base layer for modules that need to connect Odoo with external
file storage systems. A backend record centralizes storage configuration and
allows specialized addons to implement support for concrete protocols or
providers such as Amazon S3, SFTP, or compatible services.

This addon is mainly a technical dependency used by other storage-related
modules.
