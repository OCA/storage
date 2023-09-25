# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from odoo.tests.common import TransactionCase


class TestFsProductMultiMedia(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.media_content_a = b"media content a"
        cls.media_content_b = b"media content b"
        cls.media_content_c = b"media content c"
        cls.template = cls.env.ref("product.product_product_4_product_template")
        cls.product_a = cls.env.ref("product.product_product_4")
        cls.product_b = cls.env.ref("product.product_product_4b")
        cls.product_c = cls.env.ref("product.product_product_4c")
        cls.media_type_a = cls.env["fs.media.type"].create(
            {"name": "Media Type A", "code": "media_type_a"}
        )
        cls.media_type_b = cls.env["fs.media.type"].create(
            {"name": "Media Type B", "code": "media_type_b"}
        )
        cls.media_type_c = cls.env["fs.media.type"].create(
            {"name": "Media Type C", "code": "media_type_c"}
        )
        cls.media_a = cls.env["fs.media"].create(
            {
                "file": {
                    "filename": "a.txt",
                    "content": base64.b64encode(cls.media_content_a),
                },
                "media_type_id": cls.media_type_a.id,
            }
        )
        cls.media_c = cls.env["fs.media"].create(
            {
                "file": {
                    "filename": "c.txt",
                    "content": base64.b64encode(cls.media_content_c),
                },
                "media_type_id": cls.media_type_c.id,
            }
        )
        cls.media_b = cls.env["fs.media"].create(
            {
                "file": {
                    "filename": "b.txt",
                    "content": base64.b64encode(cls.media_content_b),
                },
                "media_type_id": cls.media_type_b.id,
            }
        )
        cls.is_sale_addon_installed = cls.env["ir.module.module"].search(
            [("name", "=", "sale"), ("state", "=", "installed")]
        )

    def setUp(self):
        super().setUp()
        self.temp_dir = self.env["fs.storage"].create(
            {
                "name": "Temp FS Storage",
                "protocol": "memory",
                "code": "mem_dir",
                "directory_path": "/tmp/",
                "model_xmlids": "fs_product_multi_media.model_fs_product_category_media,"
                "fs_product_multi_media.model_fs_product_media",
            }
        )

    def test_available_attribute_value(self):
        # The template have already 5 attribute values
        # see demo data of ipad
        media = self.env["fs.product.media"].new({"product_tmpl_id": self.template.id})
        expected = 4
        if self.is_sale_addon_installed:
            expected += 1
        self.assertEqual(len(media.available_attribute_value_ids), expected)

    def test_add_image_for_all_variant(self):
        self.assertEqual(len(self.product_a.variant_media_ids), 0)
        media = self.env["fs.product.media"].create(
            {
                "product_tmpl_id": self.template.id,
                "specific_file": {
                    "filename": "a.txt",
                    "content": base64.b64encode(self.media_content_a),
                },
            }
        )
        self.assertEqual(self.product_a.variant_media_ids, media)
        self.assertEqual(
            self.product_a.variant_media_ids.file.getvalue(), self.media_content_a
        )
        self.assertEqual(self.product_b.variant_media_ids, media)
        self.assertEqual(
            self.product_b.variant_media_ids.file.getvalue(), self.media_content_a
        )
        self.assertEqual(self.product_c.variant_media_ids, media)
        self.assertEqual(
            self.product_c.variant_media_ids.file.getvalue(), self.media_content_a
        )

    def test_add_media_for_white_variant(self):
        media = self.env["fs.product.media"].create(
            {
                "product_tmpl_id": self.template.id,
                "media_id": self.media_a.id,
                "attribute_value_ids": [
                    (6, 0, [self.env.ref("product.product_attribute_value_3").id])
                ],
            }
        )
        # White product should have the media
        self.assertEqual(self.product_a.variant_media_ids, media)
        self.assertEqual(self.product_c.variant_media_ids, media)
        # Black product should not have the media
        self.assertEqual(len(self.product_b.variant_media_ids), 0)

    def _create_multiple_medias(self):
        media_c = self.env["fs.product.media"].create(
            {
                "product_tmpl_id": self.template.id,
                "media_id": self.media_c.id,
                "sequence": 10,
                "link_existing": True,
            }
        )
        media_a = self.env["fs.product.media"].create(
            {
                "product_tmpl_id": self.template.id,
                "media_id": self.media_a.id,
                "attribute_value_ids": [
                    (6, 0, [self.env.ref("product.product_attribute_value_3").id])
                ],
                "sequence": 2,
                "link_existing": True,
            }
        )
        media_b = self.env["fs.product.media"].create(
            {
                "product_tmpl_id": self.template.id,
                "media_id": self.media_b.id,
                "attribute_value_ids": [
                    (6, 0, [self.env.ref("product.product_attribute_value_4").id])
                ],
                "sequence": 1,
                "link_existing": True,
            }
        )
        return media_c, media_a, media_b

    def test_add_media_for_white_and_black_variant(self):
        media_c, media_a, media_b = self._create_multiple_medias()
        # White product should have the media_a and the media_c
        self.assertEqual(self.product_a.variant_media_ids, media_a + media_c)
        self.assertEqual(self.product_c.variant_media_ids, media_a + media_c)
        # Black product should have the media_b and the media_c
        self.assertEqual(self.product_b.variant_media_ids, media_b + media_c)

    def test_drop_template_attribute_value_propagation_to_media(self):
        media_content_b = self.env["fs.product.media"].create(
            {
                "product_tmpl_id": self.template.id,
                "media_id": self.media_b.id,
                "attribute_value_ids": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("product.product_attribute_value_4").id,
                            self.env.ref("product.product_attribute_value_1").id,
                        ],
                    )
                ],
                "sequence": 10,
                "link_existing": True,
            }
        )
        # Remove Color black from variant tab:
        self.template.attribute_line_ids.sudo().filtered(
            lambda x: x.display_name == "Color"
        ).value_ids -= self.env.ref("product.product_attribute_value_4")
        # Attribute black is removed from media:
        self.assertTrue(
            self.env.ref("product.product_attribute_value_4")
            not in media_content_b.attribute_value_ids
        )

        # Remove Leg attribute line from variant tab:
        attr = self.template.attribute_line_ids.sudo().filtered(
            lambda x: x.display_name == "Legs"
        )
        attr.unlink()
        # Product media attribute values from Legs are removed:
        self.assertTrue(
            self.env.ref("product.product_attribute_value_1")
            not in media_content_b.attribute_value_ids
        )
