import logging
from odoo import models, api, _
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)


class Attachment(models.Model):
    _inherit = "ir.attachment"

    @api.model
    def _file_write(self, value, checksum):
        location = self._storage()
        if location != "hashed_db":
            return super(Attachment, self)._file_write(value, checksum)
        fname, _ = self._get_path(False, checksum)
        att = self.env["ir.attachment.content"].search([
            ("checksum", "=", fname)
        ], limit=1)
        if not att:
            self.env["ir.attachment.content"].create({
                "checksum": fname,
                "db_datas": value,
            })
        return fname

    @api.model
    def _file_read(self, checksum, bin_size=False):
        location = self._storage()
        if location != "hashed_db":
            return super(Attachment, self)._file_read(checksum, bin_size)
        att = self.env["ir.attachment.content"].search([
            ("checksum", "=", checksum)
        ])
        if not att:
            _logger.debug("File %s not found" % checksum)
            return super(Attachment, self)._file_read(checksum, bin_size)
        return att.db_datas

    @api.model
    def _file_delete(self, checksum):
        location = self._storage()
        if location == "hashed_db":
            attachments = self.search([
                ("store_fname", "=", checksum)
            ])
            if not attachments:
                self.env["ir.attachment.content"].search([
                    ("checksum", "=", checksum)
                ]).unlink()
        return super(Attachment, self)._file_delete(checksum)

    @api.model
    def force_storage(self):
        if not self.env.user._is_admin():
            raise AccessError(_("Only administrators can execute this action."))
        location = self._storage()
        if location == "hashed_db":
            # we don't know if previous storage was file system or DB:
            # we run for every attachment
            for attach in self.search([
                # trick to get every attachment, see _search method of ir.attachment
                "|", ("res_field", '=', False), ("res_field", "!=", False)
            ]):
                attach.write({
                    "datas": attach.datas,
                    # do not try to guess mimetype overwriting existing value
                    "mimetype": attach.mimetype,
                })
            return True
        else:
            return super(Attachment, self).force_storage()
