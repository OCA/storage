# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from openerp import api, fields, models


class StorageImage(models.Model):
    _name = 'storage.image'
    _description = 'Storage Image'

    owner_id = fields.Integer(
        "Owner",
        required=True)
    owner_model = fields.Char(
        required=True)
    file_ids = fields.One2many(
        'storage.file',
        'owner_id',
        'File',
        domain=lambda self: [("owner_model", "=", self._name)])
    name = fields.Char()
    alt_name = fields.Char(string="Alt Image name")
    filename = fields.Char(help='Full image name with the extension')
    data = fields.Binary(compute='_compute_image', inverse='_inverse_image')
    image_url = fields.Char(compute='_compute_url')
    image_medium_url = fields.Char(compute='_compute_url')
    image_small_url = fields.Char(compute='_compute_url')
    sequence = fields.Integer(
        default=10)
    show_technical = fields.Boolean(
        compute="_show_technical")

    @api.multi
    @api.depends("owner_id", "owner_model")
    def _show_technical(self):
        """Know if you need to show the technical fields."""
        self.show_technical = all(
            "default_owner_%s" % f not in self.env.context
            for f in ("id", "model"))

    @api.model
    def _get_storage(self):
        return NotImplemented

    def _compute_image(self):
        # TODO read image
        pass

    def _inverse_image(self):
        # TODO store image
        pass

    def _compute_url(self):
        aktest = ('http://www.akretion.com/sites/'
             '50443990c3c67e1bf3000004/theme/images/logo.png')
        for record in self:
            record.image_url = aktest
            record.image_medium_url = aktest
            record.image_small_url = aktest
        #for field in self._fields:
        #    if isinstance(field, fields.Char) and hasattr(field, 'size'):
        #        image_fields.append((field_name, field.size))
        #for record in self:
        #    for field, size in image_fields:
        #        record[field] = record.resize(size).url

    def resize(self, size):
        self.ensure_one()
        return search_or_create_public_file()
