This addon allows you to store media file into external filesystem from odoo.
It also provides is a technical mixin model to ease the creation of other models
that need to be linked to multiple medias stored into external filesystems.

The models provided by this addon are:

* ``fs.media``: a model that stores a reference to an media stored into
  an external filesystem.
* ``fs.media.relation.mixin``: an abstract model that can be used to
  as base class for models created to store an media linked to a model.
  This abstract model defines fields and methods to transparently handle
  2 cases:
  * the media is specific to the model.
  * the media is shared between multiple models and therefore is a ``fs.media`` instance linked to the mixin.
