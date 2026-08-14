# Copyright 2025 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import json
from collections import defaultdict
from datetime import date, datetime

import requests
import yaml
from pytz import UTC

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


def parse_date(origin_date):
    if not origin_date:
        return False
    final_date = origin_date
    if isinstance(final_date, date):
        final_date = datetime.combine(final_date, datetime.min.time())
    if isinstance(final_date, datetime):
        if not final_date.tzinfo:
            final_date = final_date.replace(tzinfo=UTC)
        final_date = final_date.astimezone(UTC)
        return final_date.replace(tzinfo=None).isoformat()
    return False


class ContentgridConfiguration(models.Model):
    _name = "contentgrid.configuration"
    _description = "Contentgrid Configuration"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    model_id = fields.Many2one(
        comodel_name="ir.model",
        required=True,
        ondelete="cascade",
    )
    res_model = fields.Char(
        related="model_id.model", store=True, string="Resource Model"
    )
    domain = fields.Char(default="[]")
    connection_id = fields.Many2one(
        comodel_name="contentgrid.connection", required=True
    )
    configuration_data = fields.Text(required=True)
    allow_manual_send = fields.Boolean(
        default=False,
    )
    use_contentgrid_for_storage = fields.Boolean(
        help="Use ContentGrid for storage data"
    )
    contentgrid_storage_model = fields.Char()
    contentgrid_storage_field = fields.Char()

    @api.constrains("configuration_data")
    def _check_configuration_data(self):
        for record in self:
            try:
                yaml.safe_load(record.configuration_data)
            except yaml.YAMLError as e:
                raise ValidationError(
                    _("Invalid YAML format in configuration data")
                ) from e

    def _push_to_contentgrid(self, attachment, record):
        # flake8: noqa: C901
        self.ensure_one()
        if not record.filtered_domain(safe_eval(self.domain)):
            return
        element_name = "archiveDocument"
        config = yaml.safe_load(self.configuration_data)
        processed = defaultdict(lambda: [])
        access_token = self.connection_id._get_token()
        url = self.sudo().connection_id.base_url
        partner = record._mail_get_partners()[record.id][0:]
        niss = None
        if "niss" in config:
            niss = partner[config["niss"]]
        contract_number = None
        if record._name == "sale.order" and "contract_number" in config:
            contract_number = record[config["contract_number"]]
        record_data = {
            "documentType": "ADMIN",
            "source": "ODOO",
            "subtype": "AUTRE",
            "resId": record.id,
            "resModel": record._name,
            "exId": (partner and partner.id) or 0,
            "niss": niss,
            "contractNumber": contract_number,
            "documentDate": parse_date(attachment.create_date.date()),
            "oid": attachment.id,
        }
        record_uuid = (
            self.env["contentgrid.record"]
            .sudo()
            .search(
                [
                    ("res_model", "=", attachment._name),
                    ("res_id", "=", attachment.id),
                    ("element", "=", element_name),
                    ("contentgrid_connection_id", "=", self.connection_id.id),
                ],
                limit=1,
            )
            .name
        )
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        if not record_uuid:
            response = requests.post(
                f"{url}/{element_name}s",
                headers=headers,
                data=json.dumps(record_data),
                timeout=self.connection_id._timeout,
            )
            response.raise_for_status()
            record_uuid = response.json()["id"]
            self.env["contentgrid.record"].sudo().create(
                {
                    "res_model": attachment._name,
                    "res_id": attachment.id,
                    "element": element_name,
                    "name": record_uuid,
                    "contentgrid_connection_id": self.connection_id.id,
                }
            )
        else:
            response = requests.put(
                f"{url}/{element_name}s/{record_uuid}",
                headers=headers,
                data=json.dumps(record_data),
                timeout=self.connection_id._timeout,
            )
            response.raise_for_status()
        binary_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": attachment.mimetype or "application/octet-stream",
        }
        binary_headers["Content-Disposition"] = (
            f'attachment; filename="{attachment.name}"'
        )
        requests.put(
            f"{url}/{element_name}s/{record_uuid}",
            headers=binary_headers,
            data=base64.b64decode(attachment.datas),
            timeout=self.connection_id._timeout,
        ).raise_for_status()
        processed[element_name].append(record_uuid)
        storage_model = self.contentgrid_storage_model
        if (
            self.use_contentgrid_for_storage
            and storage_model
            and not attachment.contentgrid_connection_id
        ):
            url = f"{storage_model}s/{processed[storage_model][0]}"
            attachment.write(
                {
                    "contentgrid_connection_id": self.connection_id.id,
                    "contentgrid_url": url,
                }
            )
