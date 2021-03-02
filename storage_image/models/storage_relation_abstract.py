# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


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
    # Following field are non stored field and only used for UI purpose
    add_image = fields.Image(
        compute="_compute_add_image",
        readonly=False,
    )
    add_image_name = fields.Char(
        compute="_compute_add_image",
        readonly=False,
    )
    add_type = fields.Selection(
        selection=[
            ("add", "Add a new image"),
            ("select", "Choose an existing Image"),
        ],
        default="add",
        compute="_compute_add_image",
        readonly=False,
    )

    def _compute_add_image(self):
        for record in self:
            record.add_type = "add"
            record.add_image = None
            record.add_image_name = ""

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "add_image" in vals:
                image = self.env["storage.image"].create(
                    {
                        "name": vals.pop("add_image_name", ""),
                        "data": vals.pop("add_image"),
                    }
                )
                vals["image_id"] = image.id
        return super().create(vals_list)
