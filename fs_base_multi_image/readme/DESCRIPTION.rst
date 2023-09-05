This addon is a technical addon providing a set of models to ease the
creation of other models that need to be linked to multiple images stored
into external filesystems.

The models provided by this addon are:

* ``fs.image``: a model that stores a reference to an image stored into
  an external filesystem.
* ``fs.image.relation.mixin``: an abstract model that can be used to
  as base class for models created to store an image linked to a model.
  This abstract model defines fields and methods to transparently handle
  2 cases:
  * the image is specific to the model.
  * the image is shared between multiple models and therefore is a ``fs.image`` instance linked to the mixin.
