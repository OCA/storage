# Copyright 2023 Level Prime Srl (https://levelprime.com).
# @author Roberto Fichera <roberto.fichera@levelprime.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Storage Session Redis",
    "summary": "Storage Session to Redis",
    "version": "15.0.1.0.0",
    "category": "Storage",
    "website": "https://github.com/OCA/storage",
    "author": " Robyf70, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "development_status": "Production/Stable",
    "application": False,
    "installable": True,
    "external_dependencies": {"python": ["redis"]},
    "data": [],
    "post_load": "_patch_system",
}
