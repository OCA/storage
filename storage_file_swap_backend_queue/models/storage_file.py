# Copyright 2026 Camptocamp SA
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


class StorageFile(models.Model):
    _inherit = "storage.file"

    def _swap_backend_job(self, dest_backend_id):
        """Job method: swap files to the given backend.

        :return: text summary for the job result UI.
        """
        dest_backend = self.env["storage.backend"].browse(dest_backend_id)
        if not dest_backend.exists():
            return self.env._(
                "Destination backend id=%(backend_id)d no longer exists.",
                backend_id=dest_backend_id,
            )
        # Filter out records that no longer exist
        existing = self.exists()
        result = existing._swap_backend(dest_backend)
        lines = []
        moved = result.get("moved", [])
        failed = result.get("failed", [])
        missing = self - existing
        if missing:
            failed.extend(f"ID {r.id}: record no longer exists" for r in missing)
        if moved:
            lines.append(f"Moved ({len(moved)}):")
            lines.extend(f"  - {m}" for m in moved)
        if failed:
            lines.append(f"Failed ({len(failed)}):")
            lines.extend(f"  - {f}" for f in failed)
        if not lines:
            lines.append("Nothing to swap.")
        return "\n".join(lines)
