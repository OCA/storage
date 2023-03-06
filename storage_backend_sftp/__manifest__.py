# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Storage Backend SFTP",
    "summary": "Implement SFTP Storage",
    "version": "15.0.1.0.3",
    "category": "Storage",
    "website": "https://github.com/OCA/storage",
    "author": " Akretion,Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "installable": True,
    # Place an upper bound on cryptography version to be compatible with
    # pyopenssl 19 mentioned in Odoo 15's requirements.txt. If we don't do
    # this, installing this module will try to upgrade cryptography to the latest
    # version because the minimum required version in pysaml2 (>=3.1) is greater than
    # version 2.6 (from Odoo's requirement.txt). Since cryptography/pyopenssl don't
    # declare minimum supported versions, this lead to inconsistencies.
    # https://github.com/OCA/server-auth/issues/424
    # https://github.com/OCA/storage/pull/247
    "external_dependencies": {"python": ["paramiko", "cryptography<37"]},
    "depends": ["storage_backend"],
    "data": ["views/backend_storage_view.xml"],
}
