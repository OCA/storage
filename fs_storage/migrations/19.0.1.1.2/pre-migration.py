# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from openupgradelib import openupgrade

from odoo.tools import SQL

from odoo.addons.base.models.ir_model import field_xmlid


def _get_server_env_mixin_fnames(cr, model: str) -> set[str]:
    """Return the core mixin field names present on the model."""
    possible_fnames = ("server_env_defaults", "tech_name")
    cr.execute(
        SQL(
            """
            SELECT name
            FROM ir_model_fields
            WHERE model = %(model)s
              AND name IN %(possible_fnames)s
            """,
            model=model,
            possible_fnames=possible_fnames,
        )
    )
    return {row[0] for row in cr.fetchall()}


def _get_server_env_mixin_magic_fnames(cr, model):
    """Return the dynamic server_environment helper fields for the model.

    These are the fields created on the fly by server.env.mixin:
    - x_<field_name>_env_default
    - x_<field_name>_env_is_editable
    """
    cr.execute(
        SQL(
            """
            SELECT name
            FROM ir_model_fields
            WHERE model = %(model)s
              AND (
                    name LIKE 'x_%%_env_default'
                 OR name LIKE 'x_%%_env_is_editable'
              )
            """,
            model=model,
        )
    )
    return {row[0] for row in cr.fetchall()}


@openupgrade.migrate()
def migrate(env, version):
    """Move XMLIDs to the glue module.

    This keeps the server_environment ir.model.fields metadata attached to the
    new module and preserves field values.
    """
    cr = env.cr
    if not version:
        return

    model = "fs.storage"
    old_module = "fs_storage"
    new_module = "fs_storage_environment"

    mixin_fnames = _get_server_env_mixin_fnames(cr, model)
    magic_fnames = _get_server_env_mixin_magic_fnames(cr, model)
    to_move_fnames = mixin_fnames | magic_fnames

    rename_specs = [
        (field_xmlid(old_module, model, fname), field_xmlid(new_module, model, fname))
        for fname in to_move_fnames
    ]
    openupgrade.rename_xmlids(cr, rename_specs, allow_merge=True)

    # Add noupdate to the magic_fnames, to prevent Odoo from deleting them in upgrade
    if magic_fnames:
        openupgrade.logged_query(
            cr,
            """
            UPDATE ir_model_data SET noupdate = TRUE
            WHERE module = %(module)s
            AND name IN %(names)s
            """,
            dict(
                module=new_module,
                names=tuple(
                    field_xmlid(new_module, model, fname).split(".")[1]
                    for fname in magic_fnames
                ),
            ),
        )
