# Copyright 2018 Akretion (http://www.akretion.com).
# @author Raphaël Reverdy <https://github.com/hparfr>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import _, api, fields, models


class ImageTag(models.Model):
    _name = "image.tag"
    _inherit = ["server.env.techname.mixin"]
    _description = "Image Tag"

    @api.model
    def _get_default_apply_on(self):
        active_model = self.env.context.get("active_model")
        return (
            "product"
            if active_model == "product.image.relation"
            else "category"
            if active_model == "category.image.relation"
            else False
        )

    name = fields.Char(required=True)
    apply_on = fields.Selection(
        selection=[("product", "Product"), ("category", "Category")],
        default=lambda self: self._get_default_apply_on(),
    )
    product_img_rel_ids = fields.One2many(
        comodel_name="product.image.relation",
        inverse_name="tag_id",
        string="Product Image Relations",
        readonly=True,
    )
    categ_img_rel_ids = fields.One2many(
        comodel_name="category.image.relation",
        inverse_name="tag_id",
        string="Category Image Relations",
        readonly=True,
    )
    product_tmpl_count = fields.Integer(
        string="# of Products", compute="_compute_product_tmpl_count"
    )
    product_categ_count = fields.Integer(
        string="# of Categories", compute="_compute_product_categ_count"
    )

    @api.depends("product_img_rel_ids")
    def _compute_product_tmpl_count(self):
        for rec in self:
            rec.product_tmpl_count = len(
                rec.product_img_rel_ids.mapped("product_tmpl_id")
            )

    @api.depends("categ_img_rel_ids")
    def _compute_product_categ_count(self):
        for rec in self:
            rec.product_categ_count = len(rec.categ_img_rel_ids.mapped("category_id"))

    def action_open_product_templates(self):
        self.ensure_one()
        product_templates = self.product_img_rel_ids.mapped("product_tmpl_id")
        if len(product_templates) >= 1:
            result = {
                "name": _("Products"),
                "domain": [("id", "in", product_templates.ids)],
                "res_model": "product.template",
                "type": "ir.actions.act_window",
                "view_mode": "list,form",
            }
            return result
        return {"type": "ir.actions.act_window_close"}

    def action_open_product_categories(self):
        self.ensure_one()
        product_categories = self.categ_img_rel_ids.mapped("category_id")
        if len(product_categories) >= 1:
            result = {
                "name": _("Product Categories"),
                "domain": [("id", "in", product_categories.ids)],
                "res_model": "product.category",
                "type": "ir.actions.act_window",
                "view_mode": "list,form",
            }
            return result
        return {"type": "ir.actions.act_window_close"}
