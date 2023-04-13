# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, tools

from .ir_attachment import IrAttachment


class FsStorage(models.Model):

    _inherit = "fs.storage"

    optimizes_directory_path = fields.Boolean(
        help="If checked, the directory path will be optimized to avoid "
        "too much files into the same directory. This options is used when the "
        "storage is used to store attachments. Depending on the storage, this "
        "option can be ignored. It's useful for storage based on real file. "
        "This way, files with similar properties will be stored in the same "
        "directory, avoiding overcrowding in the root directory and optimizing "
        "access times."
    )

    autovacuum_gc = fields.Boolean(
        string="Autovacuum Garbage Collection",
        default=True,
        help="If checked, the autovacuum of the garbage collection will be "
        "automatically executed when the storage is used to store attachments. "
        "Sometime, the autovacuum is to avoid when files in the storage are referenced "
        "by other systems (like a website). In such case, records in the fs.file.gc "
        "table must be manually processed.",
    )
    base_url = fields.Char(default="")
    is_directory_path_in_url = fields.Boolean(
        default=False,
        help="Normally the directory_path is for internal usage. "
        "If this flag is enabled the path will be used to compute the "
        "public URL.",
    )
    base_url_for_files = fields.Char(compute="_compute_base_url_for_files", store=True)
    backend_view_use_internal_url = fields.Boolean(
        help="Decide if Odoo backend views should use the external URL (usually a CDN) "
        "or the internal url with direct access to the storage. "
        "This could save you some money if you pay by CDN traffic."
    )

    @api.model
    @tools.ormcache("code")
    def _must_optimize_directory_path(self, code):
        return bool(
            self.search([("code", "=", code), ("optimizes_directory_path", "=", True)])
        )

    @api.model
    @tools.ormcache("code")
    def _must_autovacuum_gc(self, code):
        return bool(self.search([("code", "=", code), ("autovacuum_gc", "=", True)]))

    @api.depends("base_url", "is_directory_path_in_url")
    def _compute_base_url_for_files(self):
        for rec in self:
            if not rec.base_url:
                rec.base_url_for_files = ""
                continue
            parts = [rec.base_url]
            if rec.is_directory_path_in_url:
                parts.append(rec.directory_path)
            rec.base_url_for_files = "/".join(parts)

    @api.model
    def _get_url_for_attachment(
        self, attachment: IrAttachment, exclude_base_url: bool = False
    ) -> str | None:
        """Return the URL to access the attachment

        :param attachment: an attachment record
        :return: the URL to access the attachment
        """
        fs_storage = self.get_by_code(attachment.fs_storage_code)
        if not fs_storage:
            return None
        base_url = fs_storage.base_url_for_files
        if not base_url:
            return None
        if not exclude_base_url:
            base_url = base_url.replace(base_url, "") or "/"
        parts = [base_url, attachment.fs_filename]
        return "/".join([x.rstrip("/") for x in parts if x])
