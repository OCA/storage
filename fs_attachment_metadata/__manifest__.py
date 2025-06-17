{
    "name": "FS Attachment Metadata",
    "summary": """
        Automatic content-type metadata setting for external filesystem storage
    """,
    "description": """
        Extends FS Attachment to automatically set content-type metadata on external
        storage systems when file mimetypes are known or changed.

        Features:
        - Automatic content-type setting on file creation
        - Metadata updates when mimetype changes
        - Support for GCS and other storage backends with metadata capabilities
        - Mass action to set content-type metadata on existing attachments
    """,
    "author": "Apexive Solutions LLC",
    "website": "https://github.com/apexive/odoo-storage",
    "category": "Technical",
    "version": "16.0.1.0.0",
    "depends": ["fs_attachment"],
    "data": [
        "data/ir_actions_server.xml",
    ],
    "license": "AGPL-3",
    "installable": True,
    "auto_install": False,
}
