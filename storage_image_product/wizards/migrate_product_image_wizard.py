# Copyright 2019 ACSONE SA/NV
# Copyright 2019 Camptocamp SA

import logging
import mimetypes

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class MigrateProductImageWizard(models.TransientModel):

    _name = "storage.image.migrate.wizard"
    _description = "Wizard to migrate product images from attachments"

    template_ids = fields.Many2many(
        "product.template",
        string="Products",
        ondelete="cascade",
        help="Select none to consider them all.",
    )
    wipe_attachments_after = fields.Boolean(default=True)

    @api.multi
    def action_migrate(self):
        domain = [("res_model", "=", "product.template"), ("res_field", "=", "image")]
        if self.template_ids:
            domain.append(("res_id", "=", self.template_ids.ids))
        attachments = self.env["ir.attachment"].search(domain)
        self.migrate_product_attachment_to_storage_image(attachments)

    def migrate_product_attachment_to_storage_image(self, attachments):
        """Retrieve all products and migrate their images to storage.image records."""

        product_templates = self.env["product.template"].browse(
            attachments.mapped("res_id")
        )
        _logger.info("Found %s product's images to migrate", len(product_templates))

        self.env["component.builder"]._register_hook()

        to_delete = []
        attachments_by_template_id = {a.res_id: a for a in attachments}
        for template in product_templates:
            attachment = attachments_by_template_id.get(template.id)
            if attachment.datas:
                filename = self._filename(template, attachment)
                storage_image = self._create_storage_image_from_attachment(
                    filename, attachment
                )
                self.env["product.image.relation"].create(
                    {"product_tmpl_id": template.id, "image_id": storage_image.id}
                )
                to_delete.append(attachment.id)
        if self.wipe_attachments_after:
            self.env["ir.attachment"].browse(to_delete).unlink()

    def _create_storage_image_from_attachment(self, filename, attachment):
        _logger.info(u"Create storage image for %s", filename)
        storage_image = self.env["storage.image"].create(
            {"name": filename, "data": attachment.datas}
        )
        storage_image.refresh()
        storage_image.generate_odoo_thumbnail()
        return storage_image

    def _filename(self, template, attachment):
        filename = attachment.datas_fname
        if not filename:
            name = template.name
            extension = mimetypes.guess_extension(attachment.mimetype)
            filename = "{}{}".format(name, extension)
        return filename
