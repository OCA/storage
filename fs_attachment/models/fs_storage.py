# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import const_eval

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
    use_x_sendfile_to_serve_internal_url = fields.Boolean(
        string="Use X-Sendfile To Serve Internal Url",
        help="If checked and odoo is behind a proxy that supports x-sendfile, "
        "the content served by the attachment's internal URL will be served"
        "by the proxy using the fs_url if defined. If not, the file will be "
        "served by odoo that will stream the content read from the filesystem "
        "storage. This option is useful to avoid to serve files from odoo "
        "and therefore to avoid to load the odoo process. ",
    )
    use_as_default_for_attachments = fields.Boolean(
        help="If checked, this storage will be used to store all the attachments ",
        default=False,
    )
    force_db_for_default_attachment_rules = fields.Text(
        help="When storing attachments in an external storage, storage may be slow."
        "If the storage is used to store odoo attachments by default, this could lead "
        "to a bad user experience since small images  (128, 256) are used in Odoo "
        "in list / kanban views. We want them to be fast to read."
        "This field allows to force the store of some attachments in the odoo "
        "database. The value is a dict Where the key is the beginning of the "
        "mimetype to configure and the value is the limit in size below which "
        "attachments are kept in DB. 0 means no limit.\n"
        "Default configuration means:\n"
        "* images mimetypes (image/png, image/jpeg, ...) below 50KB are stored "
        "in database\n"
        "* application/javascript are stored in database whatever their size \n"
        "* text/css are stored in database whatever their size",
        default=lambda self: self._default_force_db_for_default_attachment_rules,
    )
    use_filename_obfuscation = fields.Boolean(
        help="If checked, the filename will be obfuscated. This option is "
        "useful to avoid to expose sensitive information trough the URL "
        "or in the remote storage. The obfuscation is done using a hash "
        "of the filename. The original filename is stored in the attachment "
        "metadata. The obfusation is to avoid if the storage is used to store "
        "files that are referenced by other systems (like a website) where "
        "the filename is important for SEO.",
    )

    _sql_constraints = [
        (
            "use_as_default_for_attachments_unique",
            "unique(use_as_default_for_attachments)",
            "Only one storage can be used as default for attachments",
        )
    ]

    @property
    def _default_force_db_for_default_attachment_rules(self) -> str:
        return '{"image/": 51200, "application/javascript": 0, "text/css": 0}'

    @api.onchange("use_as_default_for_attachments")
    def _onchange_use_as_default_for_attachments(self):
        if not self.use_as_default_for_attachments:
            self.force_db_for_default_attachment_rules = ""
        else:
            self.force_db_for_default_attachment_rules = (
                self._default_force_db_for_default_attachment_rules
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("use_as_default_for_attachments"):
                vals["force_db_for_default_attachment_rules"] = None
        return super().create(vals_list)

    def write(self, vals):
        if "use_as_default_for_attachments" in vals:
            if not vals["use_as_default_for_attachments"]:
                vals["force_db_for_default_attachment_rules"] = None
            return super().write(vals)
        return super().write(vals)

    @api.constrains(
        "force_db_for_default_attachment_rules", "use_as_default_for_attachments"
    )
    def _check_force_db_for_default_attachment_rules(self):
        for rec in self:
            if not rec.force_db_for_default_attachment_rules:
                continue
            if not rec.use_as_default_for_attachments:
                raise ValidationError(
                    _(
                        "The force_db_for_default_attachment_rules can only be set "
                        "if the storage is used as default for attachments."
                    )
                )
            try:
                const_eval(rec.force_db_for_default_attachment_rules)
            except (SyntaxError, TypeError, ValueError) as e:
                raise ValidationError(
                    _(
                        "The force_db_for_default_attachment_rules is not a valid "
                        "python dict."
                    )
                ) from e

    @api.model
    @tools.ormcache()
    def get_default_storage_code_for_attachments(self):
        """Return the code of the storage to use to store by default the attachments"""
        storage = self.search([("use_as_default_for_attachments", "=", True)], limit=1)
        if storage:
            return storage.code
        return None

    @api.model
    @tools.ormcache("code")
    def get_force_db_for_default_attachment_rules(self, code):
        """Return the rules to force the storage of some attachments in the DB

        :param code: the code of the storage
        :return: a dict where the key is the beginning of the mimetype to configure
        and the value is the limit in size below which attachments are kept in DB.
        0 means no limit.
        """
        storage = self.search([("code", "=", code)], limit=1)
        if storage and storage.force_db_for_default_attachment_rules:
            return const_eval(storage.force_db_for_default_attachment_rules)
        return {}

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

    @api.model
    @tools.ormcache("code")
    def _must_use_filename_obfuscation(self, code):
        return bool(
            self.search([("code", "=", code), ("use_filename_obfuscation", "=", True)])
        )

    @api.depends("base_url", "is_directory_path_in_url")
    def _compute_base_url_for_files(self):
        for rec in self:
            if not rec.base_url:
                rec.base_url_for_files = ""
                continue
            parts = [rec.base_url]
            if rec.is_directory_path_in_url and rec.directory_path:
                parts.append(rec.directory_path)
            rec.base_url_for_files = self._normalize_url("/".join(parts))

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
        if exclude_base_url:
            base_url = base_url.replace(fs_storage.base_url.rstrip("/"), "") or "/"
        # always remove the directory_path from the fs_file_name
        # ony if it's at the start of the filename
        fs_filename = attachment.fs_filename
        if fs_filename.startswith(fs_storage.directory_path):
            fs_filename = fs_filename.replace(fs_storage.directory_path, "")
        parts = [base_url, fs_filename]
        return self._normalize_url("/".join(parts))

    @api.model
    def _normalize_url(self, url: str) -> str:
        """Normalize the URL

        :param url: the URL to normalize
        :return: the normalized URL
        remove all the double slashes and the trailing slash except if the URL
        is only a slash (in this case we return a single slash). Avoid to remove
        the double slash in the protocol part of the URL.
        """
        if url == "/":
            return url
        parts = url.split("/")
        parts = [x for x in parts if x]
        if not parts:
            return "/"
        if parts[0].endswith(":"):
            parts[0] = parts[0] + "/"
        else:
            # we preserve the trailing slash if the URL is absolute
            parts[0] = "/" + parts[0]
        return "/".join(parts)

    def recompute_urls(self) -> None:
        """Recompute the URL of all attachments since the base_url or the
        directory_path has changed. This method must be explicitly called
        by the user since we don't want to recompute the URL on each change
        of the base_url or directory_path. We could also have cases where such
        a recompute is not wanted. For example, when you restore a database
        from production to staging, you don't want to recompute the URL of
        the attachments created in production (since the directory_path use
        in production is readonly for the staging database) but you change the
        directory_path of the staging database to ensure that all the moditications
        in staging are done in a different directory and will  not impact the
        production.
        """
        attachments = self.env["ir.attachment"].search(
            [("fs_storage_id", "in", self.ids)]
        )
        attachments._compute_fs_url()
        attachments._compute_fs_url_path()
