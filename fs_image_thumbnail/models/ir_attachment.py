# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class IrAttachment(models.Model):

    _inherit = "ir.attachment"

    thumbnail_ids = fields.One2many(
        comodel_name="fs.thumbnail",
        inverse_name="attachment_id",
        string="Thumbnails",
        readonly=True,
    )
