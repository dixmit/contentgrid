# Copyright 2025 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import requests

from odoo import fields, models


class ContentgridConnection(models.Model):
    _name = "contentgrid.connection"
    _description = "Contentgrid Connection"  # TODO
    _timeout = 10

    name = fields.Char(required=True)
    openid_url = fields.Char(groups="base.group_system", required=True)
    openid_client_id = fields.Char(groups="base.group_system", required=True)
    openid_client_secret = fields.Char(groups="base.group_system", required=True)
    base_url = fields.Char(
        help="Base URL of the Contentgrid instance without models",
        required=True,
    )
    app_url = fields.Char()
    key = fields.Char(required=True)
    public_key = fields.Json()

    def refresh_public_key(self):
        self.ensure_one()
        response = requests.get(
            f"{self.base_url}/.well-known/jwks.json",
            timeout=self._timeout,
        )
        response.raise_for_status()
        self.public_key = response.json().get("keys", [])

    def _get_token(self):
        self.ensure_one()
        data = {
            "grant_type": "client_credentials",
            "client_id": self.sudo().openid_client_id,
            "client_secret": self.sudo().openid_client_secret,
        }
        response = requests.post(
            self.sudo().openid_url, data=data, timeout=self._timeout
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def _handle_incoming(self, endpoint, data, signature):
        self.ensure_one()
        endpoint_record = (
            self.env["contentgrid.endpoint"]
            .sudo()
            .search([("connection_id", "=", self.id), ("name", "=", endpoint)], limit=1)
        )
        if not endpoint_record:
            return ""
        return getattr(
            endpoint_record,
            f"_handle_incoming_{endpoint_record.kind}_{data['trigger']}",
        )(data, signature)
