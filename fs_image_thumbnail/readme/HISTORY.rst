16.0.1.0.1 (2023-10-04)
~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- The call to the method *get_or_create_thumbnails* on the *fs.image.thumbnail.mixin*
  class returns now an ordered dictionary where the key is the original image and
  the value is a recordset of thumbnail images. The order of the dict is the order
  of the images passed to the method. This ensures that when you process the result
  of the method you can be sure that the order of the images is the same as the
  order of the images passed to the method. (`#282 <https://github.com/OCA/storage/issues/282>`_)
