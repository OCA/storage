# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

_logger = logging.getLogger(__name__)


def pre_init_hook(cr):
    """Pre init hook."""
    # add columns for computed fields to avoid useless computation by the ORM
    # when installing the module
    _logger.info("Add columns for computed fields on ir_attachment")
    cr.execute(
        """
        ALTER TABLE ir_attachment
        ADD COLUMN fs_storage_id INTEGER;
        ALTER TABLE ir_attachment
        ADD FOREIGN KEY (fs_storage_id) REFERENCES fs_storage(id);
        """
    )
    cr.execute(
        """
        ALTER TABLE ir_attachment
        ADD COLUMN fs_url VARCHAR;
        """
    )
    cr.execute(
        """
        ALTER TABLE ir_attachment
        ADD COLUMN fs_storage_code VARCHAR;
        """
    )
    _logger.info("Columns added on ir_attachment")
