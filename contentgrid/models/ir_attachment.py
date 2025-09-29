# Copyright 2025 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import requests

from odoo import api, fields, models
from odoo.http import Stream

from odoo.addons.mail.tools.discuss import Store


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    contentgrid_ids = fields.One2many(
        "contentgrid.record",
        "res_id",
        domain=[("res_model", "=", "ir.attachment")],
        string="Content Grid Data",
        ondelete="cascade",
    )
    contentgrid_connection_id = fields.Many2one("contentgrid.connection", copy=False)
    contentgrid_url = fields.Char(copy=False)

    def _push_to_contentgrid(self, manual_send=False):
        self.ensure_one()
        if self.env.context.get("contentgrid_no_push"):
            return
        if self.contentgrid_ids:
            return
        if not self.res_model or not self.res_id:
            return
        record = self.env[self.res_model].browse(self.res_id).exists()
        if not record:
            return
        domain = [
            ("model_id.model", "=", self.res_model),
            ("active", "=", True),
        ]
        if manual_send:
            domain.append(("allow_manual_send", "=", True))
        for contentgrid_config in self.env["contentgrid.configuration"].search(domain):
            contentgrid_config._push_to_contentgrid(self, record)

    @api.model_create_multi
    def create(self, vals_list):
        attachments = super().create(vals_list)
        for attachment in attachments:
            attachment._push_to_contentgrid()
        return attachments

    def write(self, vals):
        res = super().write(vals)
        if "model" in vals or "res_id" in vals:
            for attachment in self:
                attachment._push_to_contentgrid()
        return res

    def _to_store(self, store: Store, **kwargs):
        result = super()._to_store(store, **kwargs)
        for attachment in self:
            store.add(
                attachment, {"contentgrid": bool(attachment.sudo().contentgrid_ids)}
            )
        return result

    def get_contentgrid_data(self):
        self.ensure_one()
        return [
            record._get_contentgrid_data() for record in self.contentgrid_ids.sudo()
        ]

    def _to_http_stream(self):
        if self.contentgrid_connection_id and self.contentgrid_url:
            stream = Stream(
                mimetype=self.mimetype,
                download_name=self.name,
                etag=self.checksum,
                public=self.public,
            )
            stream.type = "data"
            stream.data = self.raw
            stream.last_modified = self.write_date
            stream.size = len(stream.data)
            return stream
        return super()._to_http_stream()

    @api.depends("contentgrid_connection_id", "contentgrid_url")
    def _compute_raw(self):
        for attachment in self.filtered(lambda r: r.contentgrid_connection_id):
            access_token = attachment.contentgrid_connection_id._get_token()
            headers = {
                "Authorization": f"Bearer {access_token}",
            }
            data_request = requests.get(
                f"{attachment.contentgrid_connection_id.base_url}/{attachment.contentgrid_url}",
                headers=headers,
                timeout=attachment.contentgrid_connection_id._timeout,
            )
            try:
                data_request.raise_for_status()
                attachment.raw = data_request.content
            except requests.HTTPError:
                attachment.raw = b""
        return super(
            IrAttachment, self.filtered(lambda r: not r.contentgrid_connection_id)
        )._compute_raw()

    def _set_attachment_data(self, asbytes):
        if self.contentgrid_connection_id:
            return
        return super()._set_attachment_data(asbytes)
