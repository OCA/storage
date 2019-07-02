# Copyright 2018 Akretion (http://www.akretion.com).
# @author Raphaël Reverdy <https://github.com/hparfr>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class CategoryImageRelation(models.Model):
    _name = "category.image.relation"
    _description = "Category Image Relation"

    image_id = fields.Many2one("storage.image", required=True)
    category_id = fields.Many2one("product.category")
    tag_id = fields.Many2one(
        "image.tag", domain=[("apply_on", "=", "category")]
    )

    # for kanban view
    image_name = fields.Char(related="image_id.name")
    # for kanban view
    image_url = fields.Char(related="image_id.image_medium_url")


class ImageTag(models.Model):
    _name = "image.tag"
    _description = "Image Tag"

    name = fields.Char()
