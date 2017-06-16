# -*- coding: utf-8 -*-
# © 2016 Antiun Ingeniería S.L. - Jairo Llopis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, SUPERUSER_ID
import logging

_logger = logging.getLogger(__name__)


def pre_init_hook_for_submodules(cr, model, field):
    """Moves images from single to multi mode.

    Feel free to use this as a ``pre_init_hook`` for submodules.

    :param str model:
        Model name, like ``product.template``.

    :param str img_field:
        Binary field that had the images in that :param:`model`, like
        ``image``.
    """
    env = api.Environment(cr, SUPERUSER_ID, dict())
    with cr.savepoint():
        mig_field = 'mig_' + field
        cr.execute(
            """
                ALTER TABLE %(table)s
                RENAME COLUMN %(field)s TO %(mig_field)s
            """ % {
                    "table": env[model]._table,
                    "field": field,
                    "mig_field": mig_field
                }
        )


def post_init_hook_for_submodules(cr, model, img_field, name_field):
    """Moves images from single to multi mode.

    Feel free to use this as a ``post_init_hook`` for submodules.

    :param str model:
        Model name, like ``product.template``.

    :param str img_field:
        Binary field that had the images in that :param:`model`, like
        ``image``.

    :param str name_field:
        string field that had contain an name in that :param:`model`, like
        ``name``. It will be used to build the image name in multi image mode
    """
    env = api.Environment(cr, SUPERUSER_ID, dict())
    with cr.savepoint():
        mig_field = 'mig_' + img_field
        cr.execute("""
            SELECT id, %(name)s, %(mig_field)s
            FROM %(table)s
            WHERE %(mig_field)s IS NOT NULL
        """ % {
                    "table": env[model]._table,
                    "mig_field": mig_field,
                    "name": name_field
                }
        )
        res_sql = cr.fetchall()
        for record_id, record_name, val_img in res_sql:
            vals = {
                'image_ids': [[0, 0, {
                    'image_url': val_img,
                    'name': str(record_id) + '-' + record_name,
                    'res_model': model,
                }]]
            }
            env[model].browse(record_id).write(vals)
        cr.execute("""
            ALTER TABLE %(table)s DROP COLUMN %(mig_field)s
        """ % {
                "mig_field": mig_field,
                "table": env[model]._table,
            })
