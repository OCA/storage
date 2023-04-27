# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from ..fields import FSFile


class TestModel(models.Model):

    _name = "test.model"
    _log_access = False

    fs_file = FSFile(storage_code="mem_dir")
