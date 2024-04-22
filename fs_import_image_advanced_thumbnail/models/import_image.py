from odoo import api, models

from odoo.addons.fs_image.fields import FSImageValue


class ProductImageImportWizard(models.Model):
    _inherit = "storage.import.product_image"

    @api.model
    def _post_process_image(self, image):
        thumbnail_model = self.env["fs.thumbnail"]
        res = super()._post_process_image(image)
        fs_image_value = FSImageValue(attachment=image.image.attachment)
        # CHECK ME: This values should be setup on a parameter maybe?
        thumbnail_model.get_or_create_thumbnails(
            fs_image_value, sizes=[(128, 128), (64, 64)]
        )
        return res
