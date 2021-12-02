from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        contents = env["ir.attachment.content"].search([])
        for content in contents:
            attachments = env["ir.attachment"].search(
                [
                    ("store_fname", "like", content.checksum),
                    "|",
                    ("res_field", "=", False),
                    ("res_field", "!=", False),
                ]
            )
            content.checksum = attachments[0].store_fname
