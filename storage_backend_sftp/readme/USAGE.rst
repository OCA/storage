* To connect to an sftp server, you need to create if you use it, as for an SSH connection,
  a pair of private/public keys on your Odoo instance.
* Go to Settings > Technical > Storage Backend > Storage Backend
* Create a new backend for the desired connection by filling in:

  * Backend type: SFTP
  * Host
  * Port (default: 22)
  * Login
  * Password: Here type in your password or your complete generated ssh private key
    depending on the method you choose below.
    ``-----BEGIN RSA PRIVATE KEY-----
    <KEY>
    -----END RSA PRIVATE KEY-----``
  * Authentication Method: password or private key
