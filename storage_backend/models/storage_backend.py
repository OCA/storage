# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from openerp import api, fields, models
_logger = logging.getLogger(__name__)


class StorageBackend(models.Model):
    _name = 'storage.backend'
    _inherit = 'keychain.backend'

    name = fields.Char(required=True)
    backend_type = fields.Selection([
        ('amazon-s3', 'Amazon-S3'),
        ('filestore', 'Filestore'),
        ('sftp', 'Sftp'),
        ], required=True)
    public_base_url = fields.Char()

    def _get_account(self):
        """Appelé par celui qui dépose le fichiers."""
        keychain = self.env['keychain.account']
        if self.env.user.has_group('storage.backend_access'):
            retrieve = keychain.suspend_security().retrieve
        else:
            retrieve = keychain.retrieve

        accounts = retrieve(
            [
                ['namespace', '=', 'storage_%s' % self.backend_type],
                ['technical_name', '=', self.name]
            ])
        if len(accounts) == 0:
            _logger.debug('No account found for %s' % self.backend_type)
            raise Warning("No account found based on the ")
        return accounts
