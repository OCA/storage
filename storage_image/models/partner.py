# -*- coding: utf-8 -*-

import base64
import urllib
import os
import logging
from openerp import models, fields, api, exceptions, _
from openerp import tools

_logger = logging.getLogger(__name__)

class Partner(models.Model):
    _inherit = 'res.partner'

    image_ids = fields.One2many(
        comodel_name="storage.image",
        inverse_name='res_id',
        domain=lambda self: [("res_model", "=", self._name)],
    )


class AssociatePartnerWizard(models.TransientModel):
    _name = "res.partner.wizard"

    name = fields.Char('name')
    alt_name = fields.Char('Alt name')
    the_file = fields.Binary()

    @api.multi
    def associate(self):
        _logger.warning('dans wizz associate')
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


        import pdb
        pdb.set_trace()
