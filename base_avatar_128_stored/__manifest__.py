# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Base Avatar 128 Stored",
    "summary": (
        "Work around performance issue in the partner kanban by storing avatar_128"
    ),
    "version": "18.0.1.0.0",
    "license": "LGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/storage",
    "maintainers": ["sbidoul"],
    "post_init_hook": "_precompute_avatar_128",
}
