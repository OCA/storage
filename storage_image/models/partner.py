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
