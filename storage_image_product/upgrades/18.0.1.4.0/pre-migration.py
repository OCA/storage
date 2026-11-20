# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

SECTION = "image_tag"
GLUE_MODULE = "storage_image_product_server_env"


def _has_server_env_config():
    """Tell whether the server environment holds any `image.tag` configuration.

    Both the global section (``[image_tag]``) and the per-record sections
    (``[image_tag.<tech_name>]``) are considered.
    """
    try:
        from odoo.addons.server_environment.server_env import serv_config
    except ImportError:
        return False
    return any(
        section == SECTION or section.startswith(f"{SECTION}.")
        for section in serv_config.sections()
    )


def migrate(cr, version):
    """Install the server environment glue module when it is configured."""
    if not version or not _has_server_env_config():
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    module = env["ir.module.module"].search(
        [("name", "=", GLUE_MODULE), ("state", "=", "uninstalled")]
    )
    if module:
        _logger.info(
            "Server environment configuration found for %s: installing %s",
            SECTION,
            GLUE_MODULE,
        )
        module.button_install()
