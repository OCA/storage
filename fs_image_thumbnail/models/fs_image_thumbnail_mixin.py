# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from slugify import slugify

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.fs_image.fields import FSImage, FSImageValue


class FsImageThumbnailMixin(models.AbstractModel):
    """Mixin defining what is a thumbnail image and providing a
    method to generate a thumbnail image from an image.

    """

    _name = "fs.image.thumbnail.mixin"
    _description = "Fs Image Thumbnail Mixin"

    image = FSImage("Image", required=True)
    original_image = FSImage("Original Image", compute="_compute_original_image")
    size_x = fields.Integer("X size", required=True)
    size_y = fields.Integer("Y size", required=True)
    base_name = fields.Char(
        "The base name of the thumbnail image (without extension)",
        required=True,
        help="The thumbnail image will be named as base_name "
        "+ _ + size_x + _ + size_y + . + extension.\n"
        "If not set, the base name will be the name of the original image."
        "This base name is used to find all existing thumbnail of an image generated "
        "for the same base name.",
    )

    attachment_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="Attachment",
        help="Attachment containing the original image",
        required=True,
    )
    name = fields.Char(
        compute="_compute_name",
        store=True,
    )
    mimetype = fields.Char(
        compute="_compute_mimetype",
        store=True,
    )

    @api.depends("image")
    def _compute_name(self):
        for record in self:
            record.name = record.image.name if record.image else None

    @api.depends("image")
    def _compute_mimetype(self):
        for record in self:
            record.mimetype = record.image.mimetype if record.image else None

    @api.depends("attachment_id")
    def _compute_original_image(self):
        original_image_field = self._fields["original_image"]
        for record in self:
            value = None
            if record.attachment_id:
                value = original_image_field._convert_attachment_to_cache(
                    record.attachment_id
                )
            record.original_image = value

    @api.model
    def _resize(self, image: FSImage, size_x: int, size_y: int, fmt: str = "") -> bytes:
        """Resize the given image to the given size.

        :param image: the image to resize
        :param size_x: the new width of the image
        :param size_y: the new height of the image
        :param fmt: the output format of the image. Can be PNG, JPEG, GIF, or ICO.
            Default to the format of the original image. BMP is converted to
            PNG, other formats than those mentioned above are converted to JPEG.
        :return: the resized image
        """
        # image_process only accept PNG, JPEG, GIF, or ICO as output format
        # in uppercase. Remove the dot if present and convert to uppercase.
        fmt = fmt.upper().replace(".", "")
        return image.image_process(size=(size_x, size_y), output_format=fmt)

    @api.model
    def _get_resize_format(self, image: FSImage) -> str:
        """Get the format to use to resize an image.

        :return: the format to use to resize an image
        """
        fmt = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("fs_image_thumbnail.resize_format")
        )
        return fmt or image.extension

    @api.model
    def _prepare_tumbnail(
        self, image: FSImage, size_x: int, size_y: int, base_name: str
    ) -> dict:
        """Prepare the values to create a thumbnail image from the given image.

        :param image: the image to resize
        :param size_x: the new width of the image
        :param size_y: the new height of the image
        :param base_name: the base name of the thumbnail image (without extension)
        :return: the values to create a thumbnail image
        """
        fmt = self._get_resize_format(image)
        extension = fmt
        # Add a dot before the extension if needed and convert to lowercase.
        extension = extension.lower()
        if extension and not extension.startswith("."):
            extension = "." + extension
        new_image = FSImageValue(
            value=self._resize(image, size_x, size_y, fmt),
            name="%s_%s_%s%s" % (base_name, size_x, size_y, extension),
            alt_text=image.alt_text,
        )
        return {
            "image": new_image,
            "size_x": size_x,
            "size_y": size_y,
            "base_name": base_name,
            "attachment_id": image.attachment.id,
        }

    @api.model
    def _slugify_base_name(self, base_name: str) -> str:
        """Slugify the given base name.

        :param base_name: the base name to slugify
        :return: the slugified base name
        """
        return slugify(base_name) if base_name else base_name

    @api.model
    def _get_existing_thumbnail_domain(
        self, *images: tuple[FSImageValue], base_name: str = ""
    ) -> list:
        """Get the domain to find existing thumbnail images from the given image.

        :param images: a list of images we want to find existing thumbnails
        :param base_name: the base name of the thumbnail image (without extension)
            The base name must be set when multiple images are given.
        :return: the domain to find existing thumbnail images
        """
        attachment_ids = []
        for image in images:
            if image.attachment:
                attachment_ids.append(image.attachment.id)
            else:
                raise UserError(
                    _(
                        "The image %(name)s must be attached to an attachment",
                        name=image.name,
                    )
                )
        base_name = self._get_slugified_base_name(*images, base_name=base_name)
        return [
            ("attachment_id", "in", attachment_ids),
            ("base_name", "=", base_name),
        ]

    @api.model
    def get_thumbnails(
        self, *images: tuple[FSImageValue], base_name: str = ""
    ) -> list["FsImageThumbnailMixin"]:
        """Get existing thumbnail images from the given image.

        :param images: a list of images we want to find existing thumbnails
        :param base_name: the base name of the thumbnail image (without extension)
            The base name must be set when multiple images are given.
        :return: a recordset of thumbnail images
        """
        domain = self._get_existing_thumbnail_domain(*images, base_name=base_name)
        return self.search(domain)

    @api.model
    def get_or_create_thumbnails(
        self,
        *images: tuple[FSImageValue],
        sizes: list[tuple[int, int]],
        base_name: str = ""
    ) -> list["FsImageThumbnailMixin"]:
        """Get or create a thumbnail images from the given image.

        :param images: the list of images we want to get or create thumbnails
        :param sizes: the list of sizes to use to resize the image
            (list of tuple (size_x, size_y))
        :param base_name: the base name of the thumbnail image (without extension)
            The base name must be set when multiple images are given.
        :return: a dictionary where the key is the original image and the value is
            a recordset of thumbnail images
        """
        base_name = self._get_slugified_base_name(*images, base_name=base_name)
        thumbnails = self.get_thumbnails(*images, base_name=base_name)
        thumbnails_by_attachment_id = thumbnails.partition("attachment_id")
        ret = {}
        for image in images:
            thumbnails_by_size = {
                (thumbnail.size_x, thumbnail.size_y): thumbnail
                for thumbnail in thumbnails_by_attachment_id.get(image.attachment, [])
            }
            ids_to_return = []
            for size_x, size_y in sizes:
                thumbnail = thumbnails_by_size.get((size_x, size_y))
                if not thumbnail:
                    values = self._prepare_tumbnail(image, size_x, size_y, base_name)
                    # no creation possible outside of this method -> sudo() is
                    # required since no access rights defined on create
                    thumbnail = self.sudo().create(values)
                ids_to_return.append(thumbnail.id)
            # return the thumbnails browsed in the same security context as the method
            # caller
            ret[image] = self.browse(ids_to_return)
        return ret

    @api.model
    def _get_slugified_base_name(
        self, *images: tuple[FSImageValue], base_name: str
    ) -> str:
        """Get the base name of the thumbnail image (without extension).

        :param images: the list of images we want to get the base name
        :return: the base name of the thumbnail image
        """
        if not base_name:
            if len(images) > 1:
                raise UserError(
                    _("The base name must be set when multiple images are given")
                )
            base_name = images[0].name
        return self._slugify_base_name(base_name)
