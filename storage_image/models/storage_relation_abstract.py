# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ImageRelationAbstract(models.AbstractModel):
    """Use this abstract if you want to add a relation between a model and
    storage.image ImageRelationAbstract comes with a JS widget 'image_handle'.
    Use this widget on your field in kanaban mode if you want to enable images adding
    and vignettes sequencing by drag&drop.
    """

    _name = "image.relation.abstract"
    _description = "Image Relation Abstract"
    _order = "sequence, image_id"

    sequence = fields.Integer()
    image_id = fields.Many2one("storage.image", required=True)
    # for kanban view
    image_name = fields.Char(related="image_id.name")
    # for kanban view
    image_url = fields.Char(related="image_id.image_medium_url")
