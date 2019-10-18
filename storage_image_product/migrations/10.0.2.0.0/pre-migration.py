# Copyright 2018 Akretion (http://www.akretion.com).
# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def migrate(cr, version):
    """
    Change of this 10.0.2 version:
    - Rename product.image into product.image.relation because website_sale
    module already have the same model;
    - Apply the same logic on the category.image (renamed into
    category.image.relation).
    If this module is installed, it means that website_sale module is not
    installed (otherwise, we already have an issue).
    So this migration script doesn't check if website_sale is installed.
    :param cr: database cursor
    :param version: str
    :return:
    """
    if not version:
        return
    query_product = "ALTER TABLE product_image " "RENAME TO product_image_relation;"
    query_category = "ALTER TABLE category_image " "RENAME TO category_image_relation;"
    query_seq_product = (
        "ALTER SEQUENCE product_image_id_seq "
        "RENAME TO product_image_relation_id_seq;"
    )
    query_seq_categ = (
        "ALTER SEQUENCE category_image_id_seq "
        "RENAME TO category_image_relation_id_seq;"
    )
    cr.execute(query_product)
    cr.execute(query_category)
    cr.execute(query_seq_product)
    cr.execute(query_seq_categ)
