# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

import logging

from psycopg2.extensions import AsIs

from odoo.tools.sql import column_exists

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # Get all related tables using thumb mixin
    _logger.info("Pre-computing new thumbs relations")
    cr.execute("SELECT DISTINCT res_model FROM storage_thumbnail")
    res = [x[0] for x in cr.fetchall()]
    for model in res:
        # assume table has std name
        table = model.replace(".", "_")
        for scale in ("medium", "small"):
            if not column_exists(cr, table, "thumb_%s_id" % scale):
                cr.execute(
                    """
                    ALTER TABLE
                        %s
                    ADD COLUMN
                        thumb_%s_id int4
                    REFERENCES
                        storage_thumbnail(id)
                    """,
                    (AsIs(table), AsIs(scale)),
                )
                _logger.info("Added thumb %s column to %s", scale, table)
                _store_relation(cr, table, model, scale)
                _logger.info("Computed thumb %s relation for %s", scale, table)


def _store_relation(cr, table, model, scale):
    scales = {
        "medium": (128, 128),
        "small": (64, 64),
    }
    size = scales[scale]
    query = """
        UPDATE
            %s AS rel
        SET
            thumb_%s_id = th.id
        FROM
            storage_thumbnail AS th
        WHERE
            th.res_model = %s
            AND th.size_x = %s
            AND th.size_y = %s
            AND th.res_id = rel.id
    """
    cr.execute(query, (AsIs(table), AsIs(scale), model, size[0], size[1]))
