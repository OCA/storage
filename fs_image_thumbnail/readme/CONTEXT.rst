In some specific cases you may need to generate and store thumbnails of images in Odoo.
This is the case for example when you want to provide image in specific sizes for a website
or a mobile application.

This module provides a generic way to generate thumbnails of images and store them in a
specific filesystem storage. Indeed, you could need to store the thumbnails in a different
storage than the original image (eg: store the thumbnails in a CDN) to make sure the
thumbnails are served quickly when requested by an external application and to
avoid to expose the original image storage.

This module uses the `fs_image <https://github.com/oca/storage/blob/16.0/fs_image/README.rst>`_
module to store the thumbnails in a filesystem storage.

The `shopinvader_product_image <https://github.com/shopinvader/odoo-shopinvader/
blob/16.0/shopinvader_product_image>`_ addon uses this module to generate and
store the thumbnails of the images of the products and categories to be accessible
by the website.
