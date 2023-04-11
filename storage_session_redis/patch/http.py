import json
import logging

from odoo import _, http, tools
from odoo.exceptions import ValidationError
from odoo.http import ODOO_DISABLE_SESSION_GC, OpenERPSession
from odoo.tools._vendor import sessions
from odoo.tools.func import lazy_property
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

disable_module = False

try:
    import redis
except ImportError:
    disable_module = True
    _logger.warning("Cannot import the Redis python module.")

SESSION_TIMEOUT = 24 * 60 * 60


class RedisSessionStore(sessions.SessionStore):
    def __init__(self, redis, key_template="session%s", session_class=None):
        super(RedisSessionStore, self).__init__(session_class)
        self.key_template = key_template
        self.redis = redis
        try:
            self.redis_timeout = int(tools.config["session_redis_key_expire"])
        except KeyError:
            self.redis_timeout = SESSION_TIMEOUT

    def get_session_key(self, sid):
        """
        Returns key stored in redis
        A key looks like: "sessionb'7d4f998c871459acd6fd56d27920054880fd88d2'"
        """
        if isinstance(sid, str):
            sid = sid.encode("utf-8")
        return self.key_template % sid

    def save(self, session):
        """Saves session into redis"""
        key = self.get_session_key(session.sid)
        self.redis.set(name=key, value=json.dumps(dict(session)), ex=self.redis_timeout)

    def delete(self, session):
        """Delete session on redis"""
        key = self.get_session_key(session.sid)
        return self.redis.delete(key)

    def get(self, sid):
        """Get a new session from redis or create a new one"""
        session_class = None
        if self.is_valid_key(sid):
            key = self.get_session_key(sid)
            saved = self.redis.get(key)
            if saved:
                data = json.loads(saved)
                session_class = self.session_class(data, sid, False)

        return session_class or self.new()

    def list(self):
        _logger.debug("\n\n\nSession list\n\n\n")
        session_keys = self.redis.keys(self.key_template[:-2] + "*")
        return [s[len(self.key_template) - 2 :] for s in session_keys]

    def key_exists(self, sid):
        if self.is_valid_key(sid):
            key = self.get_session_key(sid)
            return bool(self.redis.get(key))
        return False

    def migrate_from_filestore(self):
        path = tools.config.session_dir
        _logger.debug("HTTP sessions stored in: %s", path)
        sessionFileStore = sessions.FilesystemSessionStore(
            path, session_class=OpenERPSession, renew_missing=True
        )
        # Migrate all sessions to redis
        for session in sessionFileStore.list():
            if not self.key_exists(session):
                self.save(sessionFileStore.get(session))


REDIS_PARAMS = [
    ("host", str),
    ("port", int),
    ("username", str),
    ("password", str),
    ("db", int),
    ("socket_timeout", float),
    ("socket_connect_timeout", float),
    ("socket_keepalive", bool),
    ("socket_keepalive_options", str),
    ("unix_socket_path", str),
    ("encoding", str),
    ("encoding_errors", str),
    ("charset", str),
    ("errors", str),
    ("decode_responses", bool),
    ("retry_on_timeout", bool),
    ("ssl", bool),
    ("ssl_keyfile", str),
    ("ssl_certfile", str),
    ("ssl_cert_reqs", str),
    ("ssl_ca_certs", str),
    ("ssl_ca_path", str),
    ("ssl_ca_data", str),
    ("ssl_check_hostname", bool),
    ("ssl_password", str),
    ("ssl_validate_ocsp", str),
    ("ssl_validate_ocsp_stapled", bool),
    ("ssl_ocsp_context", str),
    ("ssl_ocsp_expected_cert", str),
    ("max_connections", str),
    ("single_connection_client", bool),
    ("health_check_interval", str),
    ("client_name", str),
    ("master", str),
]


def redis_get_params():
    kwargs = {}
    for k, t in REDIS_PARAMS:
        try:
            value = tools.config["session_redis_" + k]
            if t == int:
                kwargs[k] = int(value)
            elif t == float:
                kwargs[k] = float(value)
            else:
                kwargs[k] = value
        except KeyError:
            continue

    return kwargs


@lazy_property
def session_store(self):
    _logger.debug("HTTP sessions stored in Redis")
    try:
        redis_mode = tools.config.get("session_redis_mode", "redis")
        if not redis_mode:
            # session_redis_mode = False disable the feature
            raise KeyError()
        elif type(redis_mode) == str and redis_mode.lower() == "redis":
            kwargs = redis_get_params()
            # Remove the master node for sentinel mode
            if "master" in kwargs:
                kwargs.pop("master")
            r = redis.Redis(**kwargs)
        elif type(redis_mode) == str and redis_mode.lower() == "sentinel":
            kwargs = redis_get_params()
            hosts = safe_eval(kwargs["host"])
            if type(hosts) != list:
                raise ValidationError(
                    _(
                        "When redis type is set to sentinel session_redis_host "
                        "must be a list of tuples"
                    )
                )
            if "master" not in kwargs:
                raise ValidationError(
                    _("Please specify the session_redis_master when in sentinel mode")
                )
            # Host is handled differently when in sentinel mode so we pop it up
            kwargs.pop("host")
            # Initialize Sentinel
            sentinel = redis.Sentinel(hosts, sentinel_kwargs=kwargs)
            # And uses the master for all our Redis operation
            r = sentinel.master_for(kwargs["master"], **kwargs)
        else:
            raise ValidationError(
                _(
                    'Invalid session_redis_type="{}". Accepted values are "redis", '
                    '"sentinel" or "False'
                ).format(redis_mode)
            )
        # Disable the default filestore garbage collector because not needed with Redis
        # since we use automatic key expiration
        http.session_gc = lambda s: None
        # Return the redis session store
        return RedisSessionStore(r, session_class=OpenERPSession)
    except KeyError:
        # Setup http sessions
        path = tools.config.session_dir
        _logger.debug("HTTP sessions stored in: %s", path)
        if ODOO_DISABLE_SESSION_GC:
            _logger.info("Default session GC disabled, manual GC required.")
        return sessions.FilesystemSessionStore(
            path, session_class=OpenERPSession, renew_missing=True
        )


if disable_module:
    _logger.warning(
        "The store_session_redis has been disabled, please check if you have the python redis"
    )
else:
    # monkey patch the session_store on main wsgi handler by using our custom method
    http.root.session_store = session_store.__get__(http.root, http.Root)
