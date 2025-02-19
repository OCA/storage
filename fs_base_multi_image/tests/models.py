# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from odoo.addons.fs_image.fields import FSImage


class TestModel(models.Model):
    _name = "test.model"
    _description = "Test Model"
    _log_access = False

    image_ids = fields.One2many(
        string="Images",
        comodel_name="fs.relation.model.image",
        inverse_name="relation_model_id",
    )
    image = FSImage(related="image_ids.image", readonly=True, store=False)
    image_medium = FSImage(related="image_ids.image_medium", readonly=True, store=False)


class FsRelationModelImage(models.Model):
    _name = "fs.relation.model.image"
    _inherit = "fs.image.relation.mixin"
    _description = "Relation Model Image"

    relation_model_id = fields.Many2one(
        comodel_name="test.model",
        string="Test Model",
        ondelete="cascade",
    )
