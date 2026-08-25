from openupgradelib import openupgrade

from odoo import _, exceptions


@openupgrade.migrate()
def migrate(env, version):
    module = env["ir.module.module"].search(
        [("name", "=", "fs_storage_backup_environment")]
    )
    if not module:
        raise exceptions.UserError(
            _(
                "The 'fs_storage_backup_environment' module is not available. "
                "It is required to preserve the server environment managed "
                "fields of 'fs.storage'. Make it available on the "
                "addons path before upgrading 'fs_storage_backup'."
            )
        )
    if module.state == "uninstalled":
        module.button_install()
