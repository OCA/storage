# Copyright 2020 Akretion (http://www.akretion.com).
# @author Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class StorageImage(models.Model):
    _inherit = "storage.image"

    product_relation_ids = fields.One2many(
        "product.image.relation", inverse_name="image_id", string="Products"
    )
    category_relation_ids = fields.One2many(
        "category.image.relation", inverse_name="image_id", string="Categories"
    )
