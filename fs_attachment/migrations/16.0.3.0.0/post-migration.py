from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if env["ir.module.module"].search(
        [("name", "=", "server_environment"), ("state", "=", "installed")]
    ):
        openupgrade.logged_query(
            env.cr,
            """
            UPDATE ir_module_module
            SET state = 'to install'
            WHERE name = 'fs_attachment_environment' AND state = 'uninstalled'
            """,
        )
