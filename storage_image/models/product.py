# -*- coding: utf-8 -*-

import base64
import urllib
import os
import logging
from openerp import models, fields, api, exceptions, _
from openerp import tools

_logger = logging.getLogger(__name__)

class ProductImage(models.Model):
    _name = 'product.product_image'

    sequence = fields.Integer()

    image_id = fields.Many2one(
        'storage.image', required=True, ondelete='cascade',
        domain=lambda self: [
            ("res_model", "=", self.product_tmpl_id._name),
            ("res_id", "=", self.product_tmpl_id.id)
        ],
    )

    product_tmpl_id = fields.Many2one(
        'product.template', required=True, ondelete='cascade')

#    # exclusions
    product_product_id = fields.Many2many(
        comodel_name="product.product",
        domain=lambda self: [
            ("res_model", "=", self.product_tmpl_id._name),
            ("res_id", "=", self.product_tmpl_id.id)
        ],
    )  # pour filtrer

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_images = fields.One2many(
        comodel_name='product.product_image',
        inverse_name='product_tmpl_id',
    )


class AssociateProductWizard(models.TransientModel):
    _name = "product.product_image.wizard"

    name = fields.Char('name')
    alt_name = fields.Char('Alt name')
    the_file = fields.Binary()

    @api.multi
    def associate(self):
        _logger.warning('dans wizz associate')
        import pdb
        pdb.set_trace()
        # I can't set api.one because I return an action
        self.ensure_one()

        active_id = self._context['active_id']
        active_model = self._context['active_model']
        target = self.env[active_model].browse(active_id)

        img = self.env['storage.image.factory'].persist(
            name=self.name,
            alt_name=self.alt_name,
            blob=self.the_file,
            target=target)

        # for odoo
        img.ask_for_thumbnail_creation(90, 90)
        img.ask_for_thumbnail_creation(150, 150)

