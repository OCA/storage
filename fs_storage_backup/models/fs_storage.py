import logging
import traceback
from datetime import timedelta, timezone
from os import path

from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError
from odoo.service import db

_logger = logging.getLogger(__name__)


class FSStorage(models.Model):
    _name = "fs.storage"
    _inherit = ["fs.storage", "mail.thread"]  # Use queue_job_cron instead?

    use_for_backup = fields.Boolean(string="Use For Backups")
    backup_include_filestore = fields.Boolean(
        string="Include Filestore In Backup",
    )
    backup_filename_format = fields.Char(
        string="Backup Filename", default="backup-%(db)s-%(dt)s.%(ext)s"
    )
    backup_keep_time = fields.Integer(string="Keep backups of (in days)", default=7)
    backup_dir = fields.Char(string="Backup Directory", default="backups")

    @property
    def _server_env_fields(self):
        env_fields = super()._server_env_fields
        env_fields.update(
            {
                "use_for_backup": {},
                "backup_include_filestore": {},
                "backup_filename_format": {"no_default_field": False},
                "backup_keep_time": {"no_default_field": False},
                "backup_dir": {"no_default_field": False},
            }
        )
        return env_fields

    @api.constrains("backup_keep_time")
    def _constrain_backup_keep_time(self):
        if self.backup_keep_time < 1:
            raise ValidationError(
                _("Keep backups of (in days) must be greater or than 0.")
            )

    def _get_backup_format(self):
        self.ensure_one()
        return self.backup_include_filestore and "zip" or "dump"

    def _get_backup_path(self):
        self.ensure_one()
        file_ext = self._get_backup_format()
        current_datetime = fields.Datetime.now().strftime("%Y%m%d%H%M%S")
        return path.join(
            self.backup_dir,
            self.backup_filename_format
            % {"db": self.env.cr.dbname, "dt": current_datetime, "ext": file_ext},
        )

    def backup_db(self):
        self.ensure_one()
        try:
            backup_path = self._get_backup_path()
            self.fs.makedirs(self.backup_dir, exist_ok=True)
            if self.fs.exists(backup_path):
                raise Exception("File already exists (%s)." % backup_path)
            backup_file = self.fs.open(backup_path, "w")
            list_db = tools.config["list_db"]
            if not list_db:
                tools.config["list_db"] = True
            db.dump_db(
                self.env.cr.dbname,
                backup_file.buffer,
                backup_format=self._get_backup_format(),
            )
            tools.config["list_db"] = list_db
        except Exception as e:
            _logger.exception("Database backup failed: %s", e)
            self.message_post(
                subject=_("Database backup failed"),
                body="<pre>%s</pre>" % tools.html_escape(traceback.format_exc()),
                subtype_id=self.env.ref(
                    "fs_storage_backup.message_subtype_backup_failed"
                ).id,
            )

    def cleanup_old_backups(self):
        self.ensure_one()
        expiry_date = fields.Datetime.now() - timedelta(days=self.backup_keep_time)
        try:
            files = self.fs.ls(self.backup_dir, detail=False)
            for file_path in files:
                file_dt = self.fs.modified(file_path)
                file_dt = file_dt.astimezone(timezone.utc)
                file_dt = file_dt.replace(tzinfo=None)
                if file_dt < expiry_date:
                    self.fs.rm(file_path)
        except Exception as e:
            _logger.exception("Failed to clean up old backups: %s", e)
            self.message_post(
                subject=_("Failed to clean up old backups"),
                body="<pre>%s</pre>" % tools.html_escape(traceback.format_exc()),
                subtype_id=self.env.ref(
                    "fs_storage_backup.message_subtype_cleanup_failed"
                ).id,
            )

    @api.model
    def cron_backup_db(self):
        # use_for_backup is not searchable
        storages = self.search([])
        for storage in storages.filtered(lambda s: s.use_for_backup):
            storage.backup_db()
            storage.cleanup_old_backups()
