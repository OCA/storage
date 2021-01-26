# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# Part of ForgeFlow. See LICENSE file for full copyright and licensing details.
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    tags = env["image.tag"].search([])
    for tag in tags:
        tag.tech_name = env["image.tag"]._normalize_tech_name(tag.name)
