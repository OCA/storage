# Copyright 2026 Camptocamp SA
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from .common import StorageImageCommonCase


class TestSwapBackend(StorageImageCommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend_b = cls.backend.sudo().copy(
            {
                "name": "Second Backend",
                "directory_path": "image_backend_b",
            }
        )

    def test_server_action_swaps_images(self):
        image = self._create_storage_image_from_file("static/akretion-logo.png")
        action = self.env.ref(
            "storage_image.storage_image_swap_backend_server_action"
        ).sudo()
        ctx = {
            "active_model": "storage.image",
            "active_ids": image.ids,
            "active_id": image.id,
        }
        result = action.with_context(**ctx).run()
        wizard_action = result
        # Server action returns an action dict; its context targets storage.file
        # with the image's file_id.
        self.assertEqual(wizard_action["res_model"], "storage.file.swap.backend")
        self.assertEqual(wizard_action["context"]["active_model"], "storage.file")
        self.assertEqual(wizard_action["context"]["active_ids"], image.file_id.ids)
        wiz = (
            self.env["storage.file.swap.backend"]
            .sudo()
            .with_context(**wizard_action["context"])
            .create({"dest_backend_id": self.backend_b.id})
        )
        self.assertEqual(wiz.source_backend_id, image.file_id.backend_id)
        wiz.action_apply()
        self.assertEqual(image.file_id.backend_id, self.backend_b)

    def test_wizard_resolves_file_ids_from_image_model(self):
        """The base wizard's fallback maps storage.image -> file_id."""
        image = self._create_storage_image_from_file("static/akretion-logo.png")
        wiz = (
            self.env["storage.file.swap.backend"]
            .sudo()
            .with_context(active_model="storage.image", active_ids=image.ids)
            .create({})
        )
        self.assertEqual(wiz.file_ids, image.file_id)
