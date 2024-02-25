{
    "name": "Filesystem Storage Backup",
    "category": "Technical",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Onestein, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/storage",
    "depends": ["fs_storage", "mail"],
    "data": [
        "data/ir_cron_data.xml",
        "data/mail_message_subtype_data.xml",
        "views/fs_storage_view.xml",
    ],
}
