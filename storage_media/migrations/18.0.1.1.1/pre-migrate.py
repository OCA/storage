# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    _fix_missing_file_type(cr)


def _fix_missing_file_type(cr):
    _logger.info("Fixing file associated to storage.media")

    query = """
    -- Set file_type = 'media' for files linked to storage_media
    UPDATE storage_file sf
    SET file_type = 'media'
    FROM storage_media sm
    WHERE sm.file_id = sf.id
    AND (sf.file_type IS NULL OR sf.file_type = '');
    """
    cr.execute(query)
