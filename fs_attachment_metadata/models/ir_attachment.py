# models/ir_attachment.py
import logging

from odoo import models
from odoo.addons.fs_attachment.models.ir_attachment import AttachmentFileLikeAdapter

_logger = logging.getLogger(__name__)


class AttachmentFileLikeAdapterWithMetadata(AttachmentFileLikeAdapter):
    """Enhanced adapter that passes metadata when opening files for writing."""

    def _open_fs_file(self, mode):

        print("OPENFILE")
        """Override to pass metadata when opening files."""
        kwargs = {}
        if 'w' in mode and self.attachment.mimetype:
            kwargs['metadata'] = {'contentType': self.attachment.mimetype}
            _logger.debug(
                "Opening file %s with content-type metadata: %s",
                self.fs_filename,
                self.attachment.mimetype
            )

        return self.fs.open(self.fs_filename, mode, **kwargs)


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    def _set_content_type_metadata(self):
        """Set content-type metadata on external storage if supported."""
        if not self:
            return

        for attachment in self:
            if not attachment.fs_storage_id or not attachment.mimetype:
                continue

            try:
                # Use the storage's setxattrs method which handles the filesystem routing
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

        # Only update metadata if mimetype changed and we have FS attachments
        if 'mimetype' in vals:
            fs_attachments = self.filtered('fs_storage_id')
            if fs_attachments:
                fs_attachments._set_content_type_metadata()

        return result

    def open(self, mode="rb", new_version=False, **kwargs):
        """Override to use our custom adapter with metadata support."""
        if self.fs_storage_id:
            return AttachmentFileLikeAdapterWithMetadata(
                self, mode=mode, new_version=new_version, **kwargs
            )
        return super().open(mode, new_version, **kwargs)
