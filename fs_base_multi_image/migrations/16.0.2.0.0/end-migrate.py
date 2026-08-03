# Copyright 2026 ACSONE SA/NV (<https://acsone.eu>)
# Author: Laurent Mignon <laurent.mignon@acsone.eu>
# pylint: disable=odoo-addons-relative-import
import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.fs_base_multi_image.models.fs_image_relation_mixin import (
    FsImageRelationMixin,
)

try:
    from odoo.upgrade import util
except ImportError as err:
    raise ImportError(
        "This migration script requires odoo.upgrade.util.\n"
        "Please install odoo.upgrade.util to proceed with the migration.\n"
        "See https://github.com/odoo/upgrade-util/"
    ) from err


_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    for model_name in env:
        if isinstance(env[model_name], FsImageRelationMixin):
            _logger.info("Recomputing image fields for model %s", model_name)
            # first 'rename attachment for field named image_medium' to 'image_128'
            _logger.info(
                "Renaming attachments for field specific_image_medium "
                "to specific_image_128 for model %s",
                model_name,
            )
            cr.execute(
                """
                UPDATE ir_attachment
                SET res_field = 'specific_image_128'
                WHERE res_model = %s AND res_field = 'specific_image_medium'
                """,
                (model_name,),
            )
            cr.execute(
                """
                UPDATE ir_attachment
                SET index_content = 'fs_specific_image_to_recompute'
                WHERE res_model = %s AND res_field = 'specific_image'
                """,
                (model_name,),
            )

    # The actual recompute of the resized image is expensive and would block
    # this migration (and the whole `-u` run) if done here synchronously. Defer it to a
    # background cron that processes small batches
    util.create_cron(
        cr,
        "Recompute fs.image.relation.mixin resized fields",
        "ir.cron",
        """
remaining = env["fs.image.mixin"]._cron_do_migrate_resize_image_fields(
    index_content="fs_specific_image_to_recompute", res_field="specific_image", batch_size=400
)

if not remaining:
    log("All fs.image.relation.mixin resized fields have been recomputed. "
        "You can safely disable the cron.", level="warning")
""",
        interval=(10, "minutes"),
    )
