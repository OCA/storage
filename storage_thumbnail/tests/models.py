from odoo import api, fields, models


# Declare as Transient to avoid ACL missing warning
class ModelTest(models.TransientModel):

    _name = "model.test"
    _inherit = "thumbnail.mixin"
    _inherits = {"storage.file": "file_id"}
    _description = "Model test"

    alt_name = fields.Char(string="Alt Image name")
    file_id = fields.Many2one("storage.file", "File", required=True, ondelete="cascade")

    @api.model
    def _get_backend_id(self):
        return int(
            self.env["ir.config_parameter"].get_param("storage.thumbnail.backend_id")
        )

    @api.model
    def create(self, vals):
        vals["file_type"] = "thumbnail"
        if "backend_id" not in vals:
            vals.update({"backend_id": self._get_backend_id()})
        for key in ["image_medium_url", "image_small_url"]:
            if key in vals:
                vals["data"] = vals.pop(key)
        return super().create(vals)
