# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

try:
    from odoo.upgrade import util
except ImportError as error:
    raise ImportError(
        "This migration script requires odoo.upgrade.util.\n"
        "Please install odoo.upgrade.util to proceed with the migration.\n"
        "See https://github.com/odoo/upgrade-util/"
    ) from error


_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    _logger.info("Recompute main_image_id for product.template records")
    util.recompute_fields(cr, "product.template", ["main_image_id"], logger=_logger)
