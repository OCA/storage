# -*- coding: utf-8 -*-

import logging
from openerp import models, fields

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    image_ids = fields.One2many(
        comodel_name="storage.image",
        inverse_name='res_id',
        domain=lambda self: [("res_model", "=", self._name)],
    )

class ProductProduct(models.Model):
    _inherit = 'product.product'

#    exclusion_image_id = fields.Many2many(
#        comodel_name="storage.image",
#        inverse_name='product_variant_ids',
#        #domain=lambda self: [(
#        #   ("res_model", "=", self.product_tmpl_id._name),
#        #   ('res_id', '=', self.product_tmpl_id.id)
#        #],
#    )


class Image(models.Model):
    _inherit = 'storage.image'

    product_variant_ids = fields.Many2many(
        comodel_name="product.product",
        string="Visible in these variants",
        help="If you leave it empty, all variants will show this image. "
             "Selecting one or several of the available variants, you "
             "restrict the availability of the image to those variants.")
