from openupgradelib import openupgrade

from odoo import _, exceptions


@openupgrade.migrate()
def migrate(env, version):
    module = env["ir.module.module"].search([("name", "=", "storage_file_environment")])
    if not module:
        raise exceptions.UserError(
            _(
                "The 'storage_file_environment' module is not available. "
                "It is required to preserve the server environment managed "
                "fields of 'storage.backend'. Make it available on the "
                "addons path before upgrading 'storage_file'."
            )
        )
    if module.state == "uninstalled":
        module.button_install()
