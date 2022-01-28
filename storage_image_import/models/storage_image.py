# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StorageImage(models.Model):
    _inherit = "storage.image"

    imported_from_url = fields.Char(index=True)

    _sql_constraints = [
        (
            "uniq_imported_from_url",
            "unique(imported_from_url)",
            "uniq_imported_from_url must be uniq",
        )
    ]
