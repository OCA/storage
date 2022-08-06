# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class ResPartnerImageRelation(models.Model):

    _name = "res.partner.image.relation"
    _inherit = "image.relation.abstract"
    _description = "Partner Image Relation"

    res_partner_id = fields.Many2one(
        "res.partner", required=True, ondelete="cascade", index=True,
    )


class ResPartner(models.Model):

    _name = "res.partner"
    _inherit = ["res.partner", "storage.main.image.mixin"]
    _field_image_ids = "image_ids"

    image_ids = fields.One2many(
        string="Partner Images",
        comodel_name="res.partner.image.relation",
        inverse_name="res_partner_id",
    )
