from odoo.addons.fs_import_image_advanced.tests.test_import_image import (
    TestStorageImportImage,
)


class TestStorageImportImageThumbnail(TestStorageImportImage):
    def setUp(self):
        super().setUp()

    def test_thumbnail_creation(self):
        wiz = self._get_wizard()
        wiz.do_import()
        products_with_image_attachments = self.products.filtered(
            lambda x: x.default_code in ["A001", "A002"]
        )
        images = products_with_image_attachments.mapped("image_ids")
        attachments = self.env["ir.attachment"]
        for image in images:
            attachments |= image.image_id.image.attachment
        thumbnails = self.env["fs.thumbnail"]
        for attachment in attachments:
            for thumbnail in attachment.thumbnail_ids:
                thumbnails |= thumbnail
        self.assertEqual(len(thumbnails), len(attachments) * 2)
