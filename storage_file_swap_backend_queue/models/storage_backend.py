# Copyright 2026 Camptocamp SA
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class StorageBackend(models.Model):
    _inherit = "storage.backend"

    swap_backend_use_queue = fields.Boolean(
        string="Use Queue for Backend Swap",
        default=False,
        help="When enabled, swapping files to/from this backend "
        "will be dispatched as asynchronous queue jobs instead of "
        "running synchronously.",
    )
