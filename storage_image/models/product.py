# -*- coding: utf-8 -*-

import logging
from openerp import models, fields, api

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    image_ids = fields.One2many(
        comodel_name="storage.image",
        inverse_name='res_id',
        domain=lambda self: [("res_model", "=", self._name)],
    )

    image_medium = fields.Binary(
        compute='_get_image_ak',
        # only for odoo backends views
    )

    image_small = fields.Binary(
        compute='_get_image_ak',
        # only for odoo backends views
    )

    @api.multi
    @api.depends('image_ids', 'name')
    def _get_image_ak(self):
        # TODO comprendre pourquoi on peu pas
        # depdends(image_ids.sequence)
        _logger.info('dans _get_image_ak image')
        for rec in self:
            if (self.image_ids):
                self.image_medium = self.image_ids[0].image_medium
                self.image_small = self.image_ids[0].image_small


class Image(models.Model):
    _inherit = 'storage.image'

    product_variant_ids = fields.Many2many(
        comodel_name="product.product",
        string="Visible in these variants",
        help="If you leave it empty, all variants will show this image. "
             "Selecting one or several of the available variants, you "
             "restrict the availability of the image to those variants.")
