# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
import time
from inspect import Parameter, signature

from odoo.tools import ormcache

_logger = logging.getLogger(__name__)

unsafe_eval = eval


class ormcache_expiring(ormcache):
    """An :class:`~odoo.tools.ormcache` whose entries expire.

    ``odoo.tools.ormcache`` keeps an entry until something clears the registry
    caches, which is not enough for a value that is only valid for a while,
    such as a credential obtained from a remote service.

    ``expiration`` is the number of seconds an entry remains usable, given
    either as a number or, like the cache key parameters, as an expression
    evaluated against the signature of the decorated method::

        @ormcache_expiring("self.id", expiration="self.token_lifetime")
        def _get_token(self):
            ...

    Expiring is not invalidating: an outdated entry is simply treated as a
    miss, so the method is called again by the first caller that needs it
    after the entry expired.
    """

    def __init__(self, *args, expiration, **kwargs):
        super().__init__(*args, **kwargs)
        self.expiration = expiration

    def __call__(self, method):
        lookup = super().__call__(method)
        self.determine_expiration()
        return lookup

    def determine_expiration(self):
        """Determine the function that computes the lifetime of an entry."""
        if not isinstance(self.expiration, str):
            expiration = self.expiration
            self.compute_expiration = lambda *args, **kwargs: expiration
            return
        # Same approach as ormcache.determine_key: build a lambda over the
        # signature of the decorated method and evaluate the expression in it.
        args = ", ".join(
            str(param.replace(annotation=Parameter.empty, default=Parameter.empty))
            for param in signature(self.method).parameters.values()
        )
        self.compute_expiration = unsafe_eval(f"lambda {args}: {self.expiration}")

    def lookup(self, method, *args, **kwargs):
        d, key0, counter = self.lru(args[0])
        key = key0 + self.key(*args, **kwargs)
        now = time.monotonic()
        try:
            expiry, value = d[key]
            if now < expiry:
                counter.hit += 1
                return value
            # The entry outlived its expiration: recompute it, below.
            counter.miss += 1
        except KeyError:
            counter.miss += 1
        except TypeError:
            _logger.warning("cache lookup error on %r", key, exc_info=True)
            counter.err += 1
            return self.method(*args, **kwargs)
        value = self.method(*args, **kwargs)
        d[key] = (now + self.compute_expiration(*args, **kwargs), value)
        return value

    def add_value(self, *args, cache_value=None, **kwargs):
        """Override to store the expiry along with the value."""
        d, key0, _counter = self.lru(args[0])
        key = key0 + self.key(*args, **kwargs)
        expiry = time.monotonic() + self.compute_expiration(*args, **kwargs)
        d[key] = (expiry, cache_value)
