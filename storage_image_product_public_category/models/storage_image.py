# Copyright 2020 Akretion (http://www.akretion.com).
# @author Raphaël Reverdy <raphael.reverdy@akretion.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models


class StorageImage(models.Model):
    _inherit = "storage.image"

    public_category_relation_ids = fields.One2many(
        "public.category.image.relation",
        inverse_name="image_id",
        string="Public Categories",
    )
