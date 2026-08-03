# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo import api, models

from ..fields import FSImage

_logger = logging.getLogger(__name__)


class FSImageMixin(models.AbstractModel):
    _name = "fs.image.mixin"
    _description = "Image Mixin"

    image = FSImage("Image")
    # resized fields stored (as attachment) for performance

    # deprecated fields, kept for backward compatibility
    # uses specific_image_128 instead of specific_image_medium
    image_medium = FSImage("Image medium", related="image_128", store=False)

    image_1024 = FSImage(
        "Image 1024", related="image", max_width=1024, max_height=1024, store=True
    )
    image_512 = FSImage(
        "Image 512", related="image", max_width=512, max_height=512, store=True
    )
    image_256 = FSImage(
        "Image 256", related="image", max_width=256, max_height=256, store=True
    )
    image_128 = FSImage(
        "Image 128", related="image", max_width=128, max_height=128, store=True
    )

    @api.model
    def _cron_do_migrate_resize_image_fields(
        self, index_content, res_field, batch_size=100
    ):
        """Migrate image fields to the new FSImage fields.

        This method is designed to be called from a cron job to process image fields
        in batches when migrating from 1.X to 2.x where the image_medium field has
        been renamed to image_128 and new resized fields have been added.
        It processes a batch of images, resizes them, and updates their
        index_content to indicate that they have been resized.
        """
        fs_images_to_resize = self.env["ir.attachment"].search(
            [("index_content", "=", index_content), ("res_field", "=", res_field)],
            limit=batch_size + 1,
            order="write_date desc",
        )
        remaining = len(fs_images_to_resize) > batch_size

        images_to_resize = fs_images_to_resize[:batch_size]
        image_resized = self.env["ir.attachment"].browse()

        ids_by_model = {}
        for image in images_to_resize:
            if image.res_model not in ids_by_model:
                ids_by_model[image.res_model] = []
            try:
                if (
                    not image.with_prefetch([image.id])
                    .with_context(bin_size=True)
                    .datas
                ):
                    image.index_content = "no content"
                    continue
            except Exception:  # noqa: E722
                _logger.exception(
                    "Failed to read image %s for model %s", image.id, image.res_model
                )
                image.index_content = "to verify"
                continue
            ids_by_model[image.res_model].append(image.res_id)
            image_resized |= image

        for res_model, ids in ids_by_model.items():
            res_model = self.env[res_model]
            records = res_model.browse(ids)
            records.modified([res_field])

        image_resized.write({"index_content": f"{index_content}_resized"})
        self.env.flush_all()
        return remaining
