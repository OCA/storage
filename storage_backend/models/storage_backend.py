# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from functools import wraps
from openerp import _, fields, models
_logger = logging.getLogger(__name__)


def implemented_by_factory(func):
    """Call a prefixed function based on 'namespace'."""
    @wraps(func)
    def wrapper(cls, *args, **kwargs):
        fun_name = func.__name__
        fun = '_%s%s' % (cls.backend_type, fun_name)
        _logger.info('try %s' % fun)
        if not hasattr(cls, fun):
            fun = '_default%s' % (fun_name)
        return getattr(cls, fun)(*args, **kwargs)
    return wrapper


class StorageBackend(models.Model):
    _name = 'storage.backend'
    _inherit = 'keychain.backend'
    _backend_name = 'storage_backend'

    name = fields.Char(required=True)
    backend_type = fields.Selection([], required=True)  # added by subclasses
    public_base_url = fields.Char()

    def store(self, name, datas, is_base64=True, **kwargs):
        if is_base64:
            datas = base64.b64decode(datas)
        return self._store(name, datas, **kwargs)

    @implemented_by_factory
    def _store(self, name, datas, **kwargs):
        pass

    @implemented_by_factory
    def get_public_url(self, obj):
        pass
