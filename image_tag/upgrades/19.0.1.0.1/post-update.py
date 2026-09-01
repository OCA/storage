# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    module = env["ir.module.module"].search(
        [("name", "=", "image_tag_environment"), ("state", "=", "uninstalled")]
    )
    if module:
        module.button_install()
