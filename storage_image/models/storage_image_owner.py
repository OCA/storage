## -*- coding: utf-8 -*-
## © 2014 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
##        Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
## © 2015 Antiun Ingeniería S.L. - Jairo Llopis
## Copyright 2017 Akretion (http://www.akretion.com).
## @author Sébastien BEAU <sebastien.beau@akretion.com>
## License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
#from openerp import api, fields, models
#
#
#class StorageImageOwner(models.AbstractModel):
#    _name = "storage.image.owner"
#
#    image_ids = fields.One2many(
#        comodel_name='storage.image',
#        inverse_name='owner_id',
#        string='Images',
#        domain=lambda self: [("owner_model", "=", self._name)],
#        copy=True)
#    image_main_url = fields.Binary(
#        string="Main image",
#        compute="_get_multi_image",
#        store=False)
#    image_main_medium_url = fields.Binary(
#        string="Medium image",
#        compute="_get_multi_image",
#        store=False)
#    image_main_small_url = fields.Binary(
#        string="Small image",
#        compute="_get_multi_image",
#        store=False)
#
#    @api.multi
#    @api.depends('image_ids')
#    def _get_multi_image(self):
#        """Get the main image for this object.
#
#        This is provided as a compatibility layer for submodels that already
#        had one image per record.
#        """
#        for s in self:
#            # TODO use URL
#            first = s.image_ids[:1]
#            s.image_main_url = first.image_url
#            s.image_main_medium_url = first.image_medium_url
#            s.image_main_small_url = first.image_small_url
#
#    @api.multi
#    def unlink(self):
#        """Mimic `ondelete="cascade"` for multi images."""
#        images = self.mapped("image_ids")
#        result = super(StorageImageOwner, self).unlink()
#        if result and not self.env.context.get('bypass_image_removal'):
#            images.unlink()
#        return result
#