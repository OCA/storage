# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class StorageBackendCategory(models.Model):
    _name = "storage.backend.category"
    _description = "Storage Backend Category"
    _order = "name"

    name = fields.Char(required=True, index=True)
    description = fields.Text()
    backend_ids = fields.One2many("storage.backend", "categ_id", string="Backends")
