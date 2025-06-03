# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

# DON'T IMPORT THIS MODULE IN INIT TO AVOID THE CREATION OF THE MODELS
# DEFINED FOR TESTS INTO YOUR ODOO INSTANCE
from odoo import fields, models

from ..fields import FsFolder


class FsTestModel(models.Model):
    _name = "fstest.model"
    _rec_name = "name"
    _description = "fstest.model Fake Model"

    def _get_name(self, field, fs):
        return dict.fromkeys(self.ids, "custom_name")

    def _get_parent(self, field, fs):
        return dict.fromkeys(self.ids, ["custom_parent"])

    def _get_properties(self, field, fs):
        return dict.fromkeys(self.ids, {"key": "value"})

    def _fs_create(self, field, fs):
        self.fs_folder2 = "tmpfs://_create_method"

    name = fields.Char(required=True)
    fs_folder = FsFolder()
    fs_folder1 = FsFolder(
        create_parent_get="_get_parent",
        create_name_get="_get_name",
        create_additional_kwargs_get="_get_properties",
    )

    fs_folder2 = FsFolder(create_method="_fs_create")


class FsTestModelInherits(models.Model):
    _name = "fstest.model.inherits"
    _inherits = {"fstest.model": "fs_test_model_id"}
    _description = "fstest.model.inherits Fake Model"

    fs_test_model_id = fields.Many2one(
        "fstest.model", "Parent", ondelete="cascade", required=True
    )


class FsTestModelRelated(models.Model):
    _name = "fstest.model.related"
    _description = "fstest.model.related Fake Model"

    name = fields.Char(required=True)

    fs_test_model_id = fields.Many2one(
        "fstest.model", "Parent", ondelete="cascade", required=True
    )
    fs_folder1 = FsFolder(related="fs_test_model_id.fs_folder1")

    fs_folder2 = FsFolder(related="fs_test_model_id.fs_folder2")
