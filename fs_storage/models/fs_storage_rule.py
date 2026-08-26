# Copyright 2026 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FsStorageRule(models.Model):
    _name = "fs.storage.rule"
    _description = "FS Storage Dynamic Routing Rule"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    storage_id = fields.Many2one("fs.storage", required=True, ondelete="cascade")
    model_id = fields.Many2one("ir.model", required=True, ondelete="cascade")
    field_id = fields.Many2one(
        "ir.model.fields",
        ondelete="cascade",
        domain="[('model_id', '=', model_id), ('ttype', '=', 'binary')]",
        help="Leave empty to match any field (or no field) on the model.",
    )
    domain = fields.Char(
        default="[]",
        required=True,
        help="Evaluated against the resource record. The first rule "
        "(by sequence) whose domain matches wins.\n\n"
        "This domain is only evaluated when the attachment "
        "itself is created or its content is written (new version). It is "
        "not re-evaluated when the underlying record changes afterwards. "
        "An attachment created while a record matched (e.g. an invoice "
        "PDF generated at posting time, state='posted') keeps its storage "
        "even if the record later stops matching (e.g. the invoice is "
        "reset to draft). This is by design: routing is a permanent "
        "classification decided at write time, not a live reflection of "
        "the record's current state.",
    )
    active = fields.Boolean(default=True)

    @api.constrains("model_id", "field_id")
    def _check_field_belongs_to_model(self):
        for rec in self.filtered("field_id"):
            if rec.field_id.model_id != rec.model_id:
                raise ValidationError(
                    _(
                        "The field %(field)s does not belong to the model "
                        "%(model)s.",
                        field=rec.field_id.display_name,
                        model=rec.model_id.display_name,
                    )
                )
