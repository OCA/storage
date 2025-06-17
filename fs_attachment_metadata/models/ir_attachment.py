# models/ir_attachment.py
import logging
import os

from odoo import models, api

_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    def _get_datas_related_values(self, data, mimetype):
        """Override to pass mimetype to storage operations."""
        # Store mimetype in context for _storage_file_write to access
        if mimetype:
            self = self.with_context(attachment_mimetype=mimetype)

        # Call parent method which will eventually call _storage_file_write
        return super()._get_datas_related_values(data, mimetype)

    @api.model
    def _storage_file_write(self, bin_data: bytes) -> str:
        """Write the file to the filesystem storage with content-type metadata."""
        storage = self.env.context.get("storage_location") or self._storage()
        fs = self._get_fs_storage_for_code(storage)
        path = self._get_fs_path(storage, bin_data)
        dirname = os.path.dirname(path)
        if not fs.exists(dirname):
            fs.makedirs(dirname)
        fname = f"{storage}://{path}"
        kwargs = self._storage_write_option(fs)

        # Get mimetype from context
        mimetype = self.env.context.get('attachment_mimetype')

        if mimetype:
            kwargs['content_type'] = mimetype

        with fs.open(path, "wb", **kwargs) as f:
            f.write(bin_data)
        self._fs_mark_for_gc(fname)
        return fname

    def _set_content_type_metadata(self):
        """Set content-type metadata on external storage if supported."""
        for attachment in self.filtered(lambda a: a.fs_storage_id and a.mimetype):
            try:
                result = attachment.fs_storage_id.setxattrs(
                    attachment.fs_filename,
                    content_type=attachment.mimetype
                )
                if result is not None:
                    _logger.debug("Set content-type for %s", attachment.fs_filename)
            except Exception as e:
                _logger.debug("Failed to set content-type for %s: %s", attachment.fs_filename, e)

    def write(self, vals):
        """Override to set content-type metadata when mimetype changes."""
        result = super().write(vals)

        # Set metadata when mimetype changes on existing files
        if 'mimetype' in vals:
            self._set_content_type_metadata()

        return result
