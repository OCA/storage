# Copyright 2021 Camptocamp (http://www.camptocamp.com).
# @author Iván Todorovich <ivan.todorovich@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class FakeImageRelation(models.Model):
    _name = "fake.image.relation"
    _inherit = ["image.relation.abstract"]
    _description = "Fake Image Relation model used in tests"
