# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    if not version:
        return
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        contents = env['ir.attachment.content'].search([])
        for content in contents:
            attachments = env['ir.attachment'].search([
                ('store_fname', 'like', content.checksum),
                "|",
                ("res_field", '=', False),
                ("res_field", "!=", False)
            ])
            # già controllato che non ci sono state perdite di file con checksum molto simili
            content.checksum = attachments[0].store_fname
