# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StorageFile(models.Model):
    _inherit = "storage.file"

    file_type = fields.Selection(
        selection_add=[("image", "Image")], ondelete={"image": "set null"}
    )
