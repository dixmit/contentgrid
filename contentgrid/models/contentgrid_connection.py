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
    username = fields.Char(groups="base.group_system", required=True)
    password = fields.Char(groups="base.group_system", required=True)
    base_url = fields.Char(
        help="Base URL of the Contentgrid instance without models",
        required=True,
    )
    app_url = fields.Char()

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
