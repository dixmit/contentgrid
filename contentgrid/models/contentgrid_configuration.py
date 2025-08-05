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
        return final_date.isoformat()
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
        config = yaml.safe_load(self.configuration_data)
        processed = defaultdict(lambda: [])
        access_token = self.connection_id._get_token()
        url = self.sudo().connection_id.base_url
        for element_name, element_config in config.items():
            if not isinstance(element_config, dict):
                raise ValidationError(
                    _("Configuration data must be a list of dictionaries")
                )
            to_process_records = attachment
            if "compute" in element_config:
                to_process_records = safe_eval(
                    element_config["compute"],
                    {"attachment": attachment, "record": record},
                )
            if not isinstance(to_process_records, models.Model):
                raise ValidationError(_("Compute function must return a recordset"))
            for to_process_record in to_process_records:
                record_data = {}
                for field, value in element_config.get("data", {}).items():
                    parsed_value = safe_eval(
                        value, {"record": to_process_record, "parse_date": parse_date}
                    )
                    if parsed_value:
                        record_data[field] = parsed_value
                record_uuid = False
                new_record = True
                record_uuid = (
                    self.env["contentgrid.record"]
                    .sudo()
                    .search(
                        [
                            ("res_model", "=", to_process_record._name),
                            ("res_id", "=", to_process_record.id),
                            ("element", "=", element_name),
                            ("contentgrid_connection_id", "=", self.connection_id.id),
                        ],
                        limit=1,
                    )
                    .name
                )
                if record_uuid:
                    new_record = False
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                }
                if new_record:
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
                            "res_model": to_process_record._name,
                            "res_id": to_process_record.id,
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
                for binary_key, binary_value in element_config.get(
                    "binary", {}
                ).items():
                    binary_headers = {
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": safe_eval(
                            binary_value["mimetype"], {"record": to_process_record}
                        ),
                    }
                    if binary_value.get("name"):
                        filename = safe_eval(
                            binary_value["name"], {"record": to_process_record}
                        )
                        binary_headers["Content-Disposition"] = (
                            f'attachment; filename="{filename}"'
                        )
                    requests.put(
                        f"{url}/{element_name}s/{record_uuid}/{binary_key}",
                        headers=binary_headers,
                        data=base64.b64decode(
                            safe_eval(
                                binary_value["compute"], {"record": to_process_record}
                            )
                        ),
                        timeout=self.connection_id._timeout,
                    ).raise_for_status()
                processed[element_name].append(record_uuid)
        for element_name, element_config in config.items():
            for link in element_config.get("link", []):
                for origin_record in processed[element_name]:
                    for target_record in processed[link]:
                        headers = {
                            "Authorization": f"Bearer {access_token}",
                            "Content-Type": "text/uri-list",
                        }
                        response = requests.post(
                            f"{url}/{element_name}s/{origin_record}/{link}",
                            headers=headers,
                            data=f"{link}s/{target_record}",
                            timeout=self.connection_id._timeout,
                        )
                        response.raise_for_status()
