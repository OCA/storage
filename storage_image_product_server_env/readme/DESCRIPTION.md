Glue module making Server Environment features available for the image
tags of `storage_image_product`.

Image tags are referenced in the server environment configuration by
their technical name.

**This module is meant to be abandoned.** It only exists to ease the
transition for databases where image tags were configured through the
server environment, when `storage_image_product` depended on it. Do not
rely on it for new setups: it will not be migrated to future versions.
