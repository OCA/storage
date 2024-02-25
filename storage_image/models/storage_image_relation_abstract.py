# Copyright 2020 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ImageRelationAbstract(models.AbstractModel):
    """Image Relation Abstract

    Use this abstract if you want to add a relation between a model and storage.image

    This module comes with a JS widget `image_handle`. Use this widget on your field
    in kanaban mode if you want to enable adding and reordering images by drag&drop.
    """

    _name = "image.relation.abstract"
    _description = "Image Relation Abstract"
    _order = "sequence, image_id"

    sequence = fields.Integer()
    image_id = fields.Many2one("storage.image", required=True, ondelete="cascade")
    # for kanban view
    image_name = fields.Char(related="image_id.name")
    image_alt_name = fields.Char(related="image_id.alt_name")
    image_url = fields.Char(related="image_id.image_medium_url")
