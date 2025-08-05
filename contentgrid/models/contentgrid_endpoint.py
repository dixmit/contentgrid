# Copyright 2025 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

import requests

from odoo import fields, models


class ContentgridEndpoint(models.Model):
    _name = "contentgrid.endpoint"
    _description = "Contentgrid Endpoint"  # TODO

    connection_id = fields.Many2one(
        comodel_name="contentgrid.connection", required=True
    )
    name = fields.Char(required=True)
    content_type = fields.Char()
    url = fields.Char(compute="_compute_url")
    kind = fields.Selection(
        [("attachment", "Attachment"), ("record", "Record")],
        required=True,
        default="attachment",
    )
    attachment_model_field = fields.Char()
    attachment_res_id_field = fields.Char()
    attachment_data_field = fields.Char()
    attachment_filename_field = fields.Char()

    def _compute_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for record in self:
            record.url = f"{base_url}/contentgrid/{record.name}"

    def _handle_incoming_attachment_create(self, data, signature):
        """
        We do nothing here, as we will receive updates later and we don't want to handle
        race conditions with the record not being created yet.
        """
        return ""

    def _get_new_record_values(self, res_model, data):
        return {}

    def _handle_incoming_attachment_update(self, data, signature):
        related_record = self.env["contentgrid.record"].search(
            [
                ("contentgrid_connection_id", "=", self.connection_id.id),
                ("name", "=", data["new"]["id"]),
            ],
            limit=1,
        )
        if related_record:
            # Nothing to do, the record already exists
            return ""
        record = self.env[data["new"][self.attachment_model_field]]
        if data["new"].get(self.attachment_res_id_field):
            record = record.browse(data["new"][self.attachment_res_id_field]).exists()
        access_token = self.connection_id._get_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
        }
        data_request = requests.get(
            f"{data['new']['_links']['self']['href']}/{self.attachment_data_field}",
            headers=headers,
            timeout=10,
        )
        data_request.raise_for_status()
        attachment_data = data_request.content
        if not record:
            record = record.create(
                self._get_new_record_values(record._name, data["new"])
            )
        attachment = self.env["ir.attachment"].create(
            {
                "name": data["new"].get(self.attachment_filename_field, "attachment"),
                "datas": base64.b64encode(attachment_data).decode("utf-8"),
                "res_model": record._name,
                "res_id": record.id,
                "contentgrid_ids": [
                    (
                        0,
                        0,
                        {
                            "contentgrid_connection_id": self.connection_id.id,
                            "res_model": "ir.attachment",
                            "name": data["new"].get("id"),
                            "element": self.content_type or self.name,
                        },
                    )
                ],
            }
        )
        domain = [
            ("model_id.model", "=", record._name),
            ("active", "=", True),
        ]
        for contentgrid_config in self.env["contentgrid.configuration"].search(domain):
            contentgrid_config._push_to_contentgrid(attachment, record)
        return ""

    def _handle_incoming_attachment_delete(self, data, signature):
        related_record = self.env["contentgrid.record"].search(
            [
                ("contentgrid_connection_id", "=", self.connection_id.id),
                ("name", "=", data["old"]["id"]),
            ],
            limit=1,
        )
        if related_record:
            related_record.unlink()
        return ""

    def _handle_incoming_record_create(self, data, signature):
        """We will not handle creation of records for now"""
        return ""

    def _handle_incoming_record_update(self, data, signature):
        """We will not handle update of records for now"""
        return ""

    def _handle_incoming_record_delete(self, data, signature):
        related_record = self.env["contentgrid.record"].search(
            [
                ("contentgrid_connection_id", "=", self.connection_id.id),
                ("name", "=", data["old"]["id"]),
            ],
            limit=1,
        )
        if related_record:
            related_record.unlink()
        return ""
