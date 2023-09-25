This addon provides a convenient way to get and create if not exists image
thumbnails. All the logic is implemented by the  abstract model
`fs.image.thumbnail.mixin`. The main method is `get_or_create_thumbnails` which
accepts a *FSImageValue* instance, a list of thumbnail sizes and a base name.

When the method is called, it will check if the thumbnail exists for the given
sizes and base name. If not, it will create it.

The `fs.thumbnail` model provided by this addon is a concrete implementation of
the abstract model `fs.image.thumbnail.mixin`. The motivation to implement all the
logic in an abstract model is to allow developers to create their own thumbnail
models. This could be useful if you want to store the thumbnails in a different
storage since you can specify the storage to use by model on the `fs.storage`
form view.

Creating / retrieving thumbnails is as simple as:

.. code-block:: python

  from odoo.addons.fs_image.fields import FSImageValue

  # create an attachment with a image file
  attachment = self.env['ir.attachment'].create({
      'name': 'test',
      'datas': base64.b64encode(open('test.png', 'rb').read()),
      'datas_fname': 'test.png',
  })

  # create a FSImageValue instance for the attachment
  image_value = FSImageValue(attachment)

  # get or create the thumbnails
  thumbnails = self.env['fs.thumbnail'].get_or_create_thumbnails(
      image_value, [(800,600), (400, 200)], 'my base name')



If you've a model with a *FSImage* field, the call to `get_or_create_thumbnails`
is even simpler:

.. code-block:: python

  from odoo import models
  from odoo.addons.fs_image.fields import FSImage

  class MyModel(models.Model):
      _name = 'my.model'

      image = FSImage('Image')

  my_record = cls.env['my.model'].create({
      'image': open('test.png', 'rb'),
  })

  # get or create the thumbnails
  thumbnails = record.image.get_or_create_thumbnails(my_record.image,
      [(800,600), (400, 200)], 'my base name')
