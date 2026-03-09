# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

# DON'T IMPORT THIS MODULE IN __init__ TO AVOID THE CREATION OF THE MODELS
# DEFINED FOR TESTS INTO YOUR ODOO INSTANCE

from odoo import fields, models


class TestModel(models.Model):
    _name = "test.model"
    _description = "Test Model"
    _log_access = False

    image_ids = fields.One2many(
        "fs.relation.model.image",
        "relation_model_id",
        string="Images",
    )


class FsRelationModelImage(models.Model):
    _name = "fs.relation.model.image"
    _inherit = "fs.image.relation.mixin"
    _description = "Relation Model Image"
    _log_access = False

    relation_model_id = fields.Many2one(
        "test.model",
        string="Test Model",
        ondelete="cascade",
    )
