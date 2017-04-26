# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from openerp import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class StorageImage(models.Model):
    _name = 'storage.image'
    _description = 'Storage Image'
    _inherits = {'storage.file': 'file_id'}

    alt_name = fields.Char(string="Alt Image name")
    # display_name = ?
    # exifs ? auteur, date de crétation, upload, gps, mots clefs, features ?

    exifs = fields.Char()

    thumbnail_ids = fields.One2many(
        comodel_name='storage.thumbnail',
        string='Thumbnails',
        inverse_name='res_id',
        domain=lambda self: [("res_model", "=", self._name)],
    )

    the_file = fields.Binary(
        help="The file",
        inverse='_inverse_set_file',
        compute='_compute_get_file',
        store=False)

    def _inverse_set_file(self):
        _logger.warning('comupte set file [enfant]')
        blob = self.the_file + u''
        basic_data = self.backend_id.store(
            blob=blob,
            vals={},
            object_type=self.env['storage.image']
        )
        self.url = basic_data['url']
        self.checksum = basic_data['checksum']
        checksum = basic_data['checksum']

        #factory = self.env['storage.image.factory']
        #factory.persist(
        #    alt_name=self.alt_name,
        #    name=self.name,
        #    blob=self.the_file + u'',
        #    target=self  # a fixer et mettre le res_model qui va bien
        #)
        ## generate at least one thumbnail for odoo
        #self.ask_for_thumbnail_creation(90, 90)
        #self.ask_for_thumbnail_creation(150, 150)

    def _compute_get_file(self):
        _logger.warning('comupte get file [enfant]')
        return True

    def get_thumbnail(self, size_x, size_y):
        # faidrait filtrer sur thumbnail_ids au lieu de faire un domaine ?
        domain = [
            ('res_model', '=', self._name),
            ('id', '=', self.id),
            ('size_x', '=', size_x),
            ('size_y', '=', size_y)
        ]
        return self.env['storage.thumbnail'].search(domain)

    @api.multi
    def ask_for_thumbnail_creation(self, size_x, size_y):
        factory = self.env['storage.thumbnail.factory']
        kwargs = {'size_x': size_x, 'size_y': size_y}
        for img in self:
            factory.build(img, **kwargs)

    def _compute_url(self):
        _logger.info('compute_url de l\'enfant')
        return self.file_id.backend_id.get_public_url(self)

    def get_base64(self):
        return self.file_id.get_base64()
