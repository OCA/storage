# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api

from odoo.addons.server_environment.uninstall import restore_env_managed_columns

ENV_MANAGED_FIELDS = [
    "use_for_backup",
    "backup_include_filestore",
    "backup_filename_format",
    "backup_keep_time",
    "backup_dir",
]


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["fs.storage"]._preserve_not_env_managed_data(ENV_MANAGED_FIELDS)


def uninstall_hook(env):
    """Restore database columns dropped by server.env.mixin."""
    restore_env_managed_columns(
        env,
        "fs.storage",
        ENV_MANAGED_FIELDS,
    )
