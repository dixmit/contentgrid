# Copyright 2024 Dixmit
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json
import logging

import jwt
from jwt.api_jwk import PyJWKSet

from odoo.http import Controller, request, route

from odoo.addons.mail.models.discuss.mail_guest import add_guest_to_context

_logger = logging.getLogger(__name__)


class GatewayController(Controller):
    @route(
        "/contentgrid/<string:endpoint>",
        type="http",
        auth="public",
        methods=["GET", "POST"],
        csrf=False,
    )
    @add_guest_to_context
    def post_update(self, endpoint, *args, **kwargs):
        jsonrequest = json.loads(
            request.httprequest.get_data().decode(request.httprequest.charset)
        )
        contentgrid_id = request.httprequest.headers.get(
            "ContentGrid-Application-Id", ""
        )
        token = request.httprequest.headers.get("ContentGrid-Signature", "")
        if not contentgrid_id or not token:
            _logger.warning("Missing ContentGrid headers")
            return ""
        connection = (
            request.env["contentgrid.connection"]
            .sudo()
            .search([("key", "=", contentgrid_id)], limit=1)
        )
        if not connection:
            _logger.warning(
                "No connection found for ContentGrid-Application-Id %s", contentgrid_id
            )
            return ""
        if not connection.public_key:
            _logger.info("Refreshing public key for connection %s", connection.name)
            connection.refresh_public_key()
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        jwk_set = PyJWKSet(connection.public_key)
        signing_keys = [
            jwk_set_key
            for jwk_set_key in jwk_set.keys
            if jwk_set_key.public_key_use in ["sig", None] and jwk_set_key.key_id
        ]
        signing_key = None
        for key in signing_keys:
            if key.key_id == kid:
                signing_key = key
                break
        base_url = request.env["ir.config_parameter"].sudo().get_param("web.base.url")
        try:
            signature = jwt.decode(
                token,
                signing_key,
                audience=f"{base_url}/contentgrid/{endpoint}",
                algorithms=[header.get("alg")],
                leeway=60,
            )
            return connection.sudo()._handle_incoming(endpoint, jsonrequest, signature)
        except jwt.ExpiredSignatureError:
            _logger.warning("Expired signature for token with kid %s", kid)
        except jwt.InvalidAudienceError:
            _logger.warning("Invalid audience for token with kid %s", kid)
        except jwt.InvalidIssuedAtError:
            _logger.warning("Invalid issued at for token with kid %s", kid)
        except jwt.InvalidSignatureError:
            _logger.warning("Invalid signature for token with kid %s", kid)
        except Exception as e:
            _logger.error("Error decoding token with kid %s: %s", kid, str(e))
        return ""
