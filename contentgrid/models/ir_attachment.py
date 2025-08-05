# Copyright 2025 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

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

    def _push_to_contentgrid(self):
        self.ensure_one()
        if self.contentgrid_ids:
            return
        if not self.res_model or not self.res_id:
            return
        record = self.env[self.res_model].browse(self.res_id).exists()
        if not record:
            return
        for contentgrid_config in self.env["contentgrid.configuration"].search(
            [
                ("model_id.model", "=", self.res_model),
                ("active", "=", True),
            ],
        ):
            contentgrid_config._push_to_contentgrid(self, record)

    @api.model_create_multi
    def create(self, vals_list):
        attachments = super().create(vals_list)
        for attachment in attachments:
            attachment._push_to_contentgrid()
        return attachments

    def _to_store(self, store: Store, **kwargs):
        result = super()._to_store(store, **kwargs)
        for attachment in self:
            store.add(
                attachment, {"contentgrid": bool(attachment.sudo().contentgrid_ids)}
            )
        return result

    def get_contentgrid_data(self):
        self.ensure_one()
        result = []
        for contentgrid_record in self.contentgrid_ids:
            record_data = {
                "res_model": contentgrid_record.res_model,
                "res_id": contentgrid_record.res_id,
                "name": contentgrid_record.name,
            }
            result.append(record_data)
        return [
            record._get_contentgrid_data() for record in self.contentgrid_ids.sudo()
        ]
