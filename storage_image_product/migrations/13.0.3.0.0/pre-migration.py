# Copyright 2022 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """
    Remove attribute values from product relation image that are not
    used anymore in product template attributes.
    """
    openupgrade.logged_query(
        env.cr,
        """
        WITH sub AS (
            SELECT rel.product_attribute_value_id, rel.product_image_relation_id
            FROM product_attribute_value_product_image_relation_rel rel
            JOIN product_image_relation pir
                ON pir.id = rel.product_image_relation_id
            JOIN product_template_attribute_line ptal
                ON ptal.product_tmpl_id = pir.product_tmpl_id
            JOIN product_attribute_value_product_template_attribute_line_rel rel2
                ON rel2.product_template_attribute_line_id = ptal.id
            JOIN product_attribute_value pav ON (
                rel2.product_attribute_value_id = pav.id
                AND pav.attribute_id = ptal.attribute_id
                AND rel.product_attribute_value_id = pav.id
            )
        )
        DELETE FROM product_attribute_value_product_image_relation_rel rel0
        USING product_attribute_value_product_image_relation_rel rel
        LEFT JOIN sub ON (
            sub.product_attribute_value_id = rel.product_attribute_value_id
            AND sub.product_image_relation_id = rel.product_image_relation_id)
        WHERE rel0.product_attribute_value_id = rel.product_attribute_value_id
            AND rel0.product_image_relation_id = rel.product_image_relation_id
            AND sub.product_attribute_value_id IS NULL
        """,
    )
