# Copyright 2026 Christopher Rogos
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Reset fs_filename on attachments whose content is not in a fs storage.

    fs_filename used to be copied by ``ir.attachment.copy()``. A copy whose
    content went to the database or to the odoo filestore kept the
    fs_filename of its source, which made the computation of its fs_url fail.
    """
    if not version:
        return
    cr.execute(
        """
        UPDATE ir_attachment
           SET fs_filename = NULL,
               fs_url = NULL
         WHERE fs_filename IS NOT NULL
           AND (store_fname IS NULL OR store_fname NOT LIKE '%://%')
        """
    )
    _logger.info("Reset fs_filename on %s attachments not in a storage", cr.rowcount)
