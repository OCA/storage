def _patch_system():
    from . import patch
    from odoo import http, tools

    if tools.config.get("session_redis_migrate_from_filestore", False):
        http.root.session_store.migrate_from_filestore()
