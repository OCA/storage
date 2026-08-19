# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from psycopg2 import sql

from odoo import SUPERUSER_ID, api

from odoo.addons.server_environment.uninstall import restore_env_managed_columns

ENV_MANAGED_FIELDS = [
    "optimizes_directory_path",
    "autovacuum_gc",
    "base_url",
    "is_directory_path_in_url",
    "use_x_sendfile_to_serve_internal_url",
    "use_as_default_for_attachments",
    "force_db_for_default_attachment_rules",
    "use_filename_obfuscation",
    "model_xmlids",
    "field_xmlids",
]


def post_init_hook(cr, registry):
    """Preserve fallback values without violating the attachment rule constraint.

    On a fresh install, Odoo initializes the new force database rules column on
    existing storages with its non-empty default, even when the storage is not
    the default attachment storage. The preservation helper writes fields back
    through the ORM one at a time, so this temporary inconsistent state would
    trigger the constraint. Normalize the stored fallback with SQL first.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    env.cr.execute(
        sql.SQL("UPDATE {} SET {} = NULL WHERE NOT COALESCE({}, FALSE)").format(
            sql.Identifier(env["fs.storage"]._table),
            sql.Identifier("force_db_for_default_attachment_rules"),
            sql.Identifier("use_as_default_for_attachments"),
        )
    )
    env["fs.storage"]._preserve_not_env_managed_data(ENV_MANAGED_FIELDS)


def uninstall_hook(env):
    """Restore database columns dropped by server.env.mixin."""
    restore_env_managed_columns(
        env,
        "fs.storage",
        ENV_MANAGED_FIELDS,
    )
