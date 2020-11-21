# -*- coding: utf-8 -*-
# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import http
from odoo.http import request


class DataSetController(http.Controller):
    @http.route("/web/dataset/resequence_child", type="json", auth="user")
    def resequence_child(
        self, model, target_id, child_field, children_ids, field="sequence", offset=0
    ):
        """
        Based on 'resequence' function on the DataSet Odoo controller.
        The purpose is to resequence children recordset but on the parent's
        model.
        That's useful when there is a related field or a computed fields
        (with depends) where the update is triggered only if we have a write
        on the parent's record.
        :param model: str
        :param target_id: int
        :param child_field: str
        :param children_ids: list of int
        :param field: str
        :param offset: int
        :return: bool
        """
        target_model = request.env[model]
        # Ensure the child field exists on the parent.
        if not target_model.fields_get([child_field]):
            return False
        sub_target = target_model._fields.get(child_field).comodel_name
        sub_target_model = request.env[sub_target]
        # Ensure the (sequence) field exists on the child.
        if not sub_target_model.fields_get([field]):
            return False
        all_values = []
        # python 2.6 has no start parameter
        for i, record in enumerate(sub_target_model.browse(children_ids)):
            all_values.append((1, record.id, {field: i + offset}))
        return target_model.browse(target_id).write({child_field: all_values})
