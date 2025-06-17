# models/fs_storage.py
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class FSStorage(models.Model):
    _inherit = "fs.storage"

    def setxattrs(self, path, **kwargs):
        print("SETXATTRS")
        """Set extended attributes/metadata on a file if supported by the filesystem."""
        try:
            fs_system = self.fs

            # Handle RootedDirFileSystem wrapping other filesystems (like GCS)
            if hasattr(fs_system, 'fs') and hasattr(fs_system.fs, 'setxattrs'):
                # For GCS wrapped in RootedDirFileSystem, construct full gs:// path
                if hasattr(fs_system, 'path') and fs_system.fs.__class__.__name__ == 'GCSFileSystem':
                    full_path = f"gs://{fs_system.path}/{path}"
                    return fs_system.fs.setxattrs(full_path, **kwargs)
                # For other wrapped filesystems with path joining capability
                elif hasattr(fs_system, '_join'):
                    full_path = fs_system._join(path)
                    return fs_system.fs.setxattrs(full_path, **kwargs)
                # Fallback for other wrapped filesystems
                else:
                    return fs_system.fs.setxattrs(path, **kwargs)

            # Direct filesystem with setxattrs support
            elif hasattr(fs_system, 'setxattrs'):
                return fs_system.setxattrs(path, **kwargs)

            _logger.debug("Filesystem %s does not support setxattrs", type(fs_system).__name__)
            return None

        except Exception as e:
            _logger.debug("Failed to set attributes for %s: %s", path, e)
            return None

