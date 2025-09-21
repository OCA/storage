# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Fs Folder WebDAV",
    "summary": """UI improvement when managing WebDAV folder""",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/storage",
    "depends": ["fs_folder"],
    "data": [],
    "demo": [],
    "assets": {
        "web.assets_backend": [
            "fs_folder_webdav/static/src/**/*",
        ],
    },
    "maintainers": ["jguenat"],
    "external_dependencies": {"python": ["webdav4[fsspec]"]},
}
