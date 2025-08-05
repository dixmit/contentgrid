# Copyright 2025 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.tools.safe_eval import safe_eval

from odoo.addons.mail.tools.discuss import Store


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    contentgrid_record_ids = fields.One2many(
        "contentgrid.record",
        "res_id",
        domain=lambda self: [("res_model", "=", self._name)],
    )

    def _thread_to_store(self, store: Store, /, *, request_list=None, **kwargs):
        result = super()._thread_to_store(store, request_list=request_list, **kwargs)
        contentgrid_config = (
            self.env["contentgrid.configuration"]
            .search(
                [
                    ("model_id.model", "=", self._name),
                    ("active", "=", True),
                    ("allow_manual_send", "=", True),
                ],
            )
            .filtered(lambda r: self.filtered_domain(safe_eval(r.domain)))
        )
        store.add(
            self,
            {
                "contentgrid": bool(self.contentgrid_record_ids),
                "sendContentGrid": bool(contentgrid_config),
            },
            as_thread=True,
        )
        return result

    def get_contentgrid_data(self):
        self.ensure_one()
        return [
            record._get_contentgrid_data()
            for record in self.contentgrid_record_ids.sudo()
        ]

    def send_contentgrid_data(self):
        self.ensure_one()
        self.attachment_ids._push_to_contentgrid(manual_send=True)
