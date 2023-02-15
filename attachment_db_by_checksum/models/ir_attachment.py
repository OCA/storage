#  Copyright 2023 Simone Rubino - TAKOBI
#  License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, models
from odoo.exceptions import AccessError
from odoo.osv import expression

_logger = logging.getLogger(__name__)

HASHED_STORAGE_PARAMETER = "hashed_db"


class Attachment(models.Model):
    _inherit = "ir.attachment"

    @api.model
    def _file_write_by_checksum(self, bin_value, checksum):
        """Store attachment content in `Attachment content by hash`."""
        fname, full_path = self._get_path(bin_value, checksum)
        attachment_content = self.env["ir.attachment.content"].search_by_checksum(fname)
        if not attachment_content:
            self.env["ir.attachment.content"].create(
                {
                    "checksum": fname,
                    "db_datas": bin_value,
                }
            )
        return fname

    @api.model
    def _file_write(self, bin_value, checksum):
        location = self._storage()
        if location == HASHED_STORAGE_PARAMETER:
            return self._file_write_by_checksum(bin_value, checksum)
        return super()._file_write(bin_value, checksum)

    @api.model
    def _file_read_by_checksum(self, fname):
        """Read attachment content from `Attachment content by hash`."""
        attachment_content = self.env["ir.attachment.content"].search_by_checksum(fname)
        if attachment_content:
            bin_value = attachment_content.db_datas
        else:
            # Fallback on standard behavior
            _logger.debug("File %s not found" % fname)
            bin_value = super()._file_read(fname)
        return bin_value

    @api.model
    def _file_read(self, fname):
        location = self._storage()
        if location == HASHED_STORAGE_PARAMETER:
            return self._file_read_by_checksum(fname)
        return super()._file_read(fname)

    @api.model
    def _get_all_attachments_by_checksum_domain(self, fname=None):
        """Get domain for finding all the attachments.

        If `checksum` is provided,
        get domain for finding all the attachments having checksum `checksum`.
        """
        # trick to get every attachment, see _search method of ir.attachment
        domain = [
            ("id", "!=", 0),
        ]
        if fname is not None:
            checksum_domain = [
                ("store_fname", "=", fname),
            ]
            domain = expression.AND(
                [
                    domain,
                    checksum_domain,
                ]
            )
        return domain

    @api.model
    def _get_all_attachments_by_checksum(self, fname=None):
        """Get all attachments.

        If `checksum` is provided,
        get all the attachments having checksum `checksum`.
        """
        domain = self._get_all_attachments_by_checksum_domain(fname)
        invisible_menu_context = {
            "ir.ui.menu.full_list": True,
        }
        attachments = self.with_context(**invisible_menu_context).search(domain)
        return attachments

    @api.model
    def _file_delete_by_checksum(self, fname):
        """Delete attachment content in `Attachment content by hash`."""
        attachments = self._get_all_attachments_by_checksum(fname=fname)
        if not attachments:
            attachment_content = self.env["ir.attachment.content"].search_by_checksum(
                fname
            )
            attachment_content.unlink()

    @api.model
    def _file_delete(self, fname):
        location = self._storage()
        if location == HASHED_STORAGE_PARAMETER:
            self._file_delete_by_checksum(fname)
        return super()._file_delete(fname)

    @api.model
    def force_storage_by_checksum(self):
        """Copy all the attachments to `Attachment content by hash`."""
        if not self.env.is_admin():
            raise AccessError(_("Only administrators can execute this action."))

        # we don't know if previous storage was file system or DB:
        # we run for every attachment
        all_attachments = self._get_all_attachments_by_checksum()
        for attach in all_attachments:
            attach.write(
                {
                    "datas": attach.datas,
                    # do not try to guess mimetype overwriting existing value
                    "mimetype": attach.mimetype,
                }
            )
        return True

    @api.model
    def force_storage(self):
        location = self._storage()
        if location == HASHED_STORAGE_PARAMETER:
            return self.force_storage_by_checksum()
        return super().force_storage()
