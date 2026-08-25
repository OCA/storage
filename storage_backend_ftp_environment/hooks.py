# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.addons.server_environment.uninstall import restore_env_managed_columns

ENV_MANAGED_FIELDS = [
    "ftp_password",
    "ftp_login",
    "ftp_server",
    "ftp_port",
    "ftp_encryption",
    "ftp_security",
    "ftp_passive",
]


def post_init_hook(env):
    env["storage.backend"]._preserve_not_env_managed_data(ENV_MANAGED_FIELDS)


def uninstall_hook(env):
    """Restore database columns dropped by server.env.mixin."""
    restore_env_managed_columns(
        env,
        "storage.backend",
        ENV_MANAGED_FIELDS,
        field_defaults={"ftp_security": "none"},
    )
