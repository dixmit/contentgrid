# Copyright 2025 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import requests

from odoo import fields, models


class ContentgridRecord(models.Model):
    _name = "contentgrid.record"
    _description = "Contentgrid Record"

    res_id = fields.Integer(required=True)
    res_model = fields.Char(required=True)
    name = fields.Char()
    element = fields.Char()
    contentgrid_connection_id = fields.Many2one(
        "contentgrid.connection",
        required=True,
        ondelete="cascade",
    )

    def _get_contentgrid_data(self):
        self.ensure_one()
        access_token = self.contentgrid_connection_id._get_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        data = requests.get(
            f"{self.contentgrid_connection_id.base_url}/{self.element}s/{self.name}",
            headers=headers,
            timeout=self.contentgrid_connection_id._timeout,
        )
        data.raise_for_status()
        url = (
            self.contentgrid_connection_id.app_url
            or self.contentgrid_connection_id.base_url
        )
        return {
            "id": self.id,
            "name": self.name,
            "contentgrid_connection": self.contentgrid_connection_id.name,
            "data": data.json(),
            "url": f"{url}/{self.element}s/details/{self.name}",
        }
