# WebDAV upload handler for bank statements
import base64
import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

# Filenames are attacker-controlled here (auth='public' + a path segment), so
# cap the depth and reject anything that could escape the intended flat layout.
_MAX_PATH_DEPTH = 8
_MAX_UPLOAD_BYTES = 100 * 1024 * 1024


def _json_error(message, status):
    return http.Response(
        json.dumps({"error": message}),
        status=status,
        headers={"Content-Type": "application/json"},
    )


def _authenticate():
    """Validate the Bearer token and return (user, error_response).

    On failure the first value is None and error_response is a Response.
    On success, error_response is None.

    This mirrors sms_collector's _authenticate() so both public ingestion
    endpoints accept the same res.users.apikeys credential. The route is
    auth='public' because WebDAV clients cannot be relied on to complete an
    Odoo login, so the API key is the only thing standing between an anonymous
    caller and a write. Do not relax this without putting real authentication
    in front of the route.

    Uploads validate with the dedicated ``dav`` scope. DAV tokens are issued
    with that scope by ``dav_api_key_generator``, which means they cannot be
    replayed against the general RPC endpoint. Keys created with no scope (the
    default from Odoo's own API-key UI) still match, so existing clients are
    unaffected.
    """
    auth_header = request.httprequest.headers.get("Authorization")
    if not auth_header:
        return None, _json_error("No Authorization header provided", 401)
    if not auth_header.startswith("Bearer "):
        return None, _json_error("Invalid Authorization format", 401)
    api_key = auth_header.split(" ", 1)[1].strip()
    if not api_key:
        return None, _json_error("Invalid API key", 401)
    user_id = request.env["res.users.apikeys"]._check_credentials(
        scope="dav", key=api_key
    )
    if not user_id:
        return None, _json_error("Invalid API key", 401)
    user = request.env["res.users"].sudo().browse(user_id)
    if not user.exists() or not user.active:
        return None, _json_error("Invalid API key", 401)
    return user, None


class WebDAVUploadController(http.Controller):

    @http.route('/upload/dav/<path:subpath>', type='http', auth='public', methods=['PUT', 'PROPFIND', 'MKCOL', 'OPTIONS'], csrf=False, priority=100)
    def handle_webdav_upload(self, subpath, **kwargs):
        """Handle WebDAV requests for bank statement uploads."""
        method = request.httprequest.method
        _logger.info(f"WebDAV {method} request: {subpath}")

        # Handle OPTIONS (pre-flight). Deliberately ahead of authentication:
        # a client must be able to discover capabilities before it has a
        # credential, and this response discloses nothing.
        if method == 'OPTIONS':
            return http.Response('', headers={
                'Allow': 'PUT, GET, HEAD, DELETE, PROPFIND, MKCOL, MOVE, COPY, OPTIONS',
                'DAV': '1,2',
            })

        user, err = _authenticate()
        if err:
            return err

        # Handle PROPFIND (directory listing)
        if method == 'PROPFIND':
            return http.Response('', status=207, headers={'Content-Type': 'application/xml'})

        # Handle MKCOL (directory creation)
        if method == 'MKCOL':
            return http.Response('', status=201)

        # Handle PUT (file upload)
        if method == 'PUT':
            try:
                parts = [p for p in subpath.rstrip('/').split('/') if p]
                if not parts:
                    return _json_error("No filename in path", 400)
                if len(parts) > _MAX_PATH_DEPTH:
                    return _json_error("Path too deep", 400)
                if any(p in ('.', '..') for p in parts):
                    return _json_error("Invalid path segment", 400)
                filename = parts[-1]

                # cache=False is required, not an optimisation choice.
                #
                # Werkzeug parses form-encoded request bodies when the Content-Type
                # is application/x-www-form-urlencoded or multipart/form-data, and
                # that consumes the input stream. A later get_data() then returns
                # b"" and the request looks like an empty upload. curl sends the
                # former by default when no Content-Type is given, so a plain
                # `curl -T file` produced:
                #
                #     {"error": "Empty body"}   400
                #
                # for a request carrying a perfectly good file. Caching the raw
                # body first is what makes the upload work whatever Content-Type
                # the client picks.
                file_data = request.httprequest.get_data(cache=False)
                if not file_data:
                    # Separate "no body at all" from "body consumed upstream", so
                    # the 400 says something actionable.
                    if (request.httprequest.content_length or 0) > 0:
                        return _json_error(
                            "Request body was consumed before it could be read; "
                            "retry with an explicit non-form Content-Type",
                            400,
                        )
                    return _json_error("Empty body", 400)
                if len(file_data) > _MAX_UPLOAD_BYTES:
                    return _json_error("File too large", 413)

                attachment = request.env['ir.attachment'].with_user(user).sudo().create({
                    'name': filename,
                    'datas': base64.b64encode(file_data),
                    'type': 'binary',
                    'res_model': 'ir.attachment',
                    'public': False,
                })

                _logger.info(
                    "WebDAV upload successful: %s by user %s (attachment id: %s)",
                    filename, user.login, attachment.id,
                )
                return http.Response('', status=201, headers={
                    'Location': f'/attachment/{attachment.id}',
                })
            except Exception as e:
                _logger.error(f"WebDAV upload failed: {str(e)}")
                return http.Response(f'Upload failed: {str(e)}', status=500)

        return http.Response('Method not allowed', status=405)

    @http.route('/contact/submit', type='http', auth='public', methods=['POST'], csrf=False)
    def handle_contact_form(self, **post):
        """Handle contact form submission."""
        try:
            name = post.get('name', '').strip()
            email = post.get('email', '').strip()
            message = post.get('message', '').strip()

            if not all([name, email, message]):
                return http.Response('Missing required fields', status=400)

            # Send email via mail.mail
            mail_values = {
                'subject': f'New Contact Form Submission from {name}',
                'body_html': f'<p><strong>Name:</strong> {name}</p><p><strong>Email:</strong> {email}</p><p><strong>Message:</strong></p><p>{message.replace(chr(10), "<br/>")}</p>',
                'email_from': email,
                'email_to': request.env.user.company_id.email or 'contact@example.com',
            }
            request.env['mail.mail'].sudo().create(mail_values).send()

            _logger.info(f"Contact form submitted by {name} ({email})")
            return http.Response('<h1>Thank you!</h1><p>Your message has been sent successfully.</p>', status=200)
        except Exception as e:
            _logger.error(f"Contact form error: {str(e)}")
            return http.Response(f'Error: {str(e)}', status=500)
