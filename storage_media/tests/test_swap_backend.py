# Copyright 2026 Camptocamp SA
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64

from odoo.addons.component.tests.common import TransactionComponentCase


class TestSwapBackend(TransactionComponentCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend_a = cls.env.ref("storage_backend.default_storage_backend")
        cls.backend_b = cls.backend_a.sudo().copy(
            {
                "name": "Second Backend",
                "directory_path": "media_backend_b",
            }
        )

    def _create_media(self, name="m1.txt", data=b"data"):
        return self.env["storage.media"].create(
            {"name": name, "data": base64.b64encode(data)}
        )

    def test_server_action_swaps_media(self):
        media = self._create_media()
        action = self.env.ref(
            "storage_media.storage_media_swap_backend_server_action"
        ).sudo()
        result = action.with_context(
            active_model="storage.media",
            active_ids=media.ids,
            active_id=media.id,
        ).run()
        self.assertEqual(result["res_model"], "storage.file.swap.backend")
        self.assertEqual(result["context"]["active_ids"], media.file_id.ids)
        wiz = (
            self.env["storage.file.swap.backend"]
            .sudo()
            .with_context(**result["context"])
            .create({"dest_backend_id": self.backend_b.id})
        )
        wiz.action_apply()
        self.assertEqual(media.file_id.backend_id, self.backend_b)

    def test_wizard_resolves_file_ids_from_media_model(self):
        media = self._create_media()
        wiz = (
            self.env["storage.file.swap.backend"]
            .sudo()
            .with_context(active_model="storage.media", active_ids=media.ids)
            .create({})
        )
        self.assertEqual(wiz.file_ids, media.file_id)
