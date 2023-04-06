{
    "name": "Storage Image Backend Migration",
    "version": "14.0.1.0.0",
    "summary": "Migrate src backend to destination backend",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "company": "ForgeFlow",
    "development_status": "Alpha",
    "maintainer": "HviorForgeFlow",
    "website": "https://github.com/OCA/storage",
    "category": "Product",
    "depends": ["storage_file", "storage_image", "queue_job"],
    "external_dependencies": {
        "python": ["python-magic", "validators"],
        "deb": ["libmagic1"],
    },
    "data": [
        "security/ir.model.access.csv",
        "data/queue_job_channel_data.xml",
        "data/queue_job_function_data.xml",
        "views/storage_image_backend_migration_wizard_views.xml",
    ],
    "license": "AGPL-3",
    "installable": True,
}
