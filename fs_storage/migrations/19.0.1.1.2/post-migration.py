# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """Install the glue module once fs_storage upgrade succeeded."""
    module = env["ir.module.module"].search(
        [
            ("name", "=", "fs_storage_environment"),
            ("state", "=", "uninstalled"),
        ],
        limit=1,
    )
    if not module:
        return
    module.button_install()
