# -*- coding: utf-8 -*-
# © 2014 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#        Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
# © 2015 Antiun Ingeniería S.L. - Jairo Llopis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models


class Owner(models.AbstractModel):
    _name = "storage.image.owner"
    _description = "Storage Image Owner"

    image_ids = fields.One2many(
        comodel_name='storage.image',
        inverse_name='res_id',
        string='Images',
        domain=lambda self: [("res_model", "=", self._name)],
        copy=True)
    image_url = fields.Char(
        string="Main image",
        compute="_compute_main_image_url",
        store=True)
    image_medium_url = fields.Char(
        string="Medium image",
        compute="_compute_main_image_url",
        store=True)
    image_small_url = fields.Char(
        string="Small image",
        compute="_compute_main_image_url",
        store=True)

    def _has_onchange(self, field, other_fields):
        # Remove onchange on image_ids fields to avoid
        # useless request with big quantity of data
        if field.name == 'image_ids':
            return False
        else:
            return super(Owner, self)._has_onchange(field, other_fields)

    # TODO FIXME
    # @api.depends('image_ids.sequence')
    @api.multi
    def _compute_main_image_url(self):
        for s in self:
            first = s.image_ids[:1]
            s.image_url = first.image_url
            s.image_medium_url = first.image_medium_url
            s.image_small_url = first.image_small_url

    @api.multi
    def unlink(self):
        """Mimic `ondelete="cascade"` for multi images."""
        images = self.mapped("image_ids")
        result = super(Owner, self).unlink()
        if result and not self.env.context.get('bypass_image_removal'):
            images.unlink()
        return result


class OwnerCompatibility(models.AbstractModel):
    _inherit = "storage.image.owner"
    _name = "storage.image.owner.compatibility"
    _description = "Storage Image Owner Compatibility"

    image_main = fields.Binary(
        string="Main image",
        compute="_compute_main_image",
        store=False)
    image_main_medium = fields.Binary(
        string="Medium image",
        compute="_compute_main_image_medium",
        store=False)
    image_main_small = fields.Binary(
        string="Small image",
        compute="_compute_main_image_small",
        store=False)

    # reading image cost bandwidth we do not add a @api.depend here
    # to avoid useless read
    @api.multi
    def _compute_main_image(self):
        self._compute_main_image_for('image_main')

    @api.multi
    def _compute_main_image_medium(self):
        self._compute_main_image_for('image_main_medium')

    @api.multi
    def _compute_main_image_small(self):
        self._compute_main_image_for('image_main_small')

    def _compute_main_image_for(self, field):
        for record in self:
            for image in record.image_ids:
                if field == 'image_main':
                    record.image_main = image.datas
                elif field == 'image_main_medium':
                    record.image_main_medium = \
                        image._get_medium_thumbnail().datas
                elif field == 'image_main_small':
                    record.image_main_small =\
                        image._get_small_thumbnail().datas
                break
