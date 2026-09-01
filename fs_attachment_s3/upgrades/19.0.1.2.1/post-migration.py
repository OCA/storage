from openupgradelib import openupgrade

from odoo import exceptions


@openupgrade.migrate()
def migrate(env, version):
    module = env["ir.module.module"].search(
        [("name", "=", "fs_attachment_s3_environment")]
    )
    if not module:
        raise exceptions.UserError(
            env._(
                "The 'fs_attachment_s3_environment' module is not available. "
                "It is required to preserve the server environment managed "
                "fields of 'fs.storage'. Make it available on the "
                "addons path before upgrading 'fs_attachment_s3'."
            )
        )
    if module.state == "uninstalled":
        module.button_install()
