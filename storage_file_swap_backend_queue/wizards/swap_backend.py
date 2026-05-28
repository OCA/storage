# Copyright 2026 Camptocamp SA
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models

DEFAULT_SWAP_BATCH_SIZE = 5
SWAP_BATCH_SIZE_PARAM = "storage_file_swap_backend_queue.swap_backend_batch_size"


class StorageFileSwapBackend(models.TransientModel):
    _inherit = "storage.file.swap.backend"

    def _action_apply(self):
        """Override to dispatch swap via queue jobs instead of synchronous."""
        batch_size = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(SWAP_BATCH_SIZE_PARAM, DEFAULT_SWAP_BATCH_SIZE)
        )
        self.file_ids.delayable()._swap_backend_job(self.dest_backend_id.id).split(
            batch_size
        ).delay()
