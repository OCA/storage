# Copyright 2026 Camptocamp SA
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StorageFileSwapBackend(models.TransientModel):
    _name = "storage.file.swap.backend"
    _description = "Swap storage files between backends"

    source_backend_id = fields.Many2one(
        "storage.backend",
        string="Source Storage",
        readonly=True,
    )
    dest_backend_id = fields.Many2one(
        "storage.backend",
        string="Destination Storage",
        domain="[('id', '!=', source_backend_id)]",
    )
    file_ids = fields.Many2many(
        "storage.file",
        string="Files",
        domain="[('backend_id', '=', source_backend_id)]",
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self.env.context.get("active_model")
        active_ids = self.env.context.get("active_ids") or []
        file_ids = self._resolve_file_ids(active_model, active_ids)
        if not file_ids:
            return res
        files = self.env["storage.file"].browse(file_ids)
        backends = files.mapped("backend_id")
        if len(backends) > 1:
            raise UserError(
                self.env._(
                    "All selected records must belong to the same source "
                    "storage backend. Found: %s"
                )
                % ", ".join(backends.mapped("name"))
            )
        res["source_backend_id"] = backends.id
        res["file_ids"] = [(6, 0, files.ids)]
        return res

    @api.model
    def _resolve_file_ids(self, active_model, active_ids):
        """Map selected records to underlying storage.file ids.

        Override in modules adding new models inheriting storage.file via
        ``_inherits`` (e.g. storage.image, storage.media).
        """
        if not active_ids:
            return []
        if active_model == "storage.file":
            return list(active_ids)
        model = self.env.get(active_model)
        if model is not None and "file_id" in model._fields:
            return model.browse(active_ids).mapped("file_id").ids
        return []

    def action_apply(self):
        self.ensure_one()
        if not self.file_ids:
            raise UserError(self.env._("Please select at least one file."))
        if not self.dest_backend_id:
            raise UserError(self.env._("Please select a destination storage."))
        if self.dest_backend_id == self.source_backend_id:
            raise UserError(self.env._("Destination storage must differ from source."))
        self.file_ids._swap_backend(self.dest_backend_id)
        return {"type": "ir.actions.act_window_close"}
