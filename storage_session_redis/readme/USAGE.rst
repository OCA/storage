The module support both Redis and Sentinel mode for HA advanced setup, this can be done by setting
the config variable as redis or sentinel or False to disable the module

* session_redis_mode

Normal redis functionality (default) set as:

session_redis_mode = redis

To get the sentinel functionality set it as:

session_redis_mode = sentinel

Or to disable the storage session redis module:

session_redis_mode = False

To set automatic expire for a particolar session, set the conf variable below with a value > 0

* session_redis_key_expire

To better tune redis configuration mode, some config options are available
See below the Redis optional parameters, real Redis configuration are prefixed by *session_redis_*

* session_redis_host
* session_redis_port
* session_redis_username
* session_redis_password
* session_redis_db
* session_redis_socket_timeout
* session_redis_socket_connect_timeout
* session_redis_socket_keepalive
* session_redis_socket_keepalive_options
* session_redis_unix_socket_path
* session_redis_encoding
* session_redis_encoding_errors
* session_redis_charset
* session_redis_errors
* session_redis_decode_responses
* session_redis_retry_on_timeout
* session_redis_ssl
* session_redis_ssl_keyfile
* session_redis_ssl_certfile
* session_redis_ssl_cert_reqs
* session_redis_ssl_ca_certs
* session_redis_ssl_ca_path
* session_redis_ssl_ca_data
* session_redis_ssl_check_hostname
* session_redis_ssl_password
* session_redis_ssl_validate_ocsp
* session_redis_ssl_validate_ocsp_stapled
* session_redis_ssl_ocsp_context
* session_redis_ssl_ocsp_expected_cert
* session_redis_max_connections
* session_redis_single_connection_client
* session_redis_health_check_interval
* session_redis_client_name

When the config session_redis_mode is set to ``sentinel`` the ``session_redis_host`` must be set as

* session_redis_host = ``[('Host-A', Port-A), ('Host-B', Port-B), ... ('Host-N', Port-N)]``

which represent a list of available Redis instance within the HA configuration.

Furthermore the variable below must be set to the master host name used for all the HA operations

* session_redis_master

such as

session_redis_master = MyMaster

The above Redis config variable will be used in ``Sentinel`` mode as ``sentinel_kwargs`` parameter when instantiating Sentinel

* Migration from Session Filestore

Migration from standard odoo Session Filestore can be performed by setting the following configuration variable:

``session_redis_migrate_from_filestore = True``

The migration is performed as Odoo ``post_load`` action. The given session ID is migrated only if not already present on Redis
