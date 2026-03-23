# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
def migrate(cr, version):
    """Install fs_storage_environment during fs_storage upgrade."""

    cr.execute(
        """
        UPDATE ir_module_module
           SET state = 'to install'
         WHERE name = 'fs_storage_environment'
           AND state = 'uninstalled'
           AND EXISTS (
               SELECT 1
                 FROM ir_module_module
                WHERE name = 'fs_storage'
                  AND state IN ('installed', 'to upgrade')
           )
           AND EXISTS (
               SELECT 1
                 FROM ir_module_module
                WHERE name = 'server_environment'
                  AND state IN ('installed', 'to upgrade')
           )
        """
    )
