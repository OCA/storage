# Copyright 2018 Akretion (http://www.akretion.com).
# Author: Sylvain Calador (<https://www.akretion.com>)
# Author: Saritha Sahadevan (<https://www.cybrosys.com>)
# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Import Storage product image",
    "version": "14.0.1.0.3",
    "summary": "Import product images using CSV",
    "author": "Akretion, Camptocamp, Odoo Community Association (OCA)",
    "company": "Akretion",
    "maintainer": "Akretion",
    "website": "https://github.com/OCA/storage",
    "category": "Product",
    "depends": ["storage_image_product", "queue_job"],
    "external_dependencies": {
        "python": ["python-magic", "validators"],
        "deb": ["libmagic1"],
    },
    "data": [
        "data/ir_cron.xml",
        "data/queue_job_channel_data.xml",
        "data/queue_job_function_data.xml",
        "security/ir_model_access.xml",
        "views/import_product_image_view.xml",
        "views/report_html.xml",
    ],
    "license": "AGPL-3",
    "installable": True,
}
