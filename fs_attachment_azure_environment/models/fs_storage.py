# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class FsStorage(models.Model):
    _inherit = "fs.storage"

    @property
    def _server_env_fields(self):
        """Override to include Azure specific fields."""
        fields = super()._server_env_fields
        fields.update(
            {
                "azure_uses_signed_url_for_x_sendfile": {},
                "azure_signed_url_expiration": {},
                "azure_delegation_key_expiration": {},
            }
        )
        return fields
