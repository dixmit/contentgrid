# Copyright 2025 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from unittest.mock import patch

import requests

from odoo.tests.common import TransactionCase

CONFIGURATION_DATA = """
attachment:
    data:
        name: record.name
        checksum: record.checksum
    binary:
        data:
            compute: record.datas
            name: record.name
            mimetype: record.mimetype
partner:
    compute: record
    data:
        name: record.name
        vat: record.vat
    link:
    - attachment
"""


class TestContentgrid(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.openid_url = "https://example.com/openid"
        cls.base_url = "https://example.com/api"
        cls.request_id = 1
        cls.connection = cls.env["contentgrid.connection"].create(
            {
                "name": "Test Connection",
                "openid_url": cls.openid_url,
                "openid_client_id": "client_id",
                "openid_client_secret": "client_secret",
                "base_url": cls.base_url,
                "key": "test_key",
            }
        )
        cls.configuration = cls.env["contentgrid.configuration"].create(
            {
                "name": "Test Configuration",
                "model_id": cls.env.ref("base.model_res_partner").id,
                "connection_id": cls.connection.id,
                "active": True,
                "configuration_data": CONFIGURATION_DATA,
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})

    def _patched_post(self):
        def _post(url, *args, **kwargs):
            response = requests.Response()
            response.status_code = 200
            if url == self.openid_url:
                response._content = b'{"access_token": "test_token"}'
            else:
                self.request_id += 1
                response._content = f'{{"id": "{self.request_id}"}}'.encode()
            return response

        return _post

    def _patched_put(self):
        def _put(url, *args, **kwargs):
            response = requests.Response()
            response.status_code = 200
            self.request_id += 1
            response._content = f'{{"id": "{self.request_id}"}}'.encode()
            return response

        return _put

    def test_1(self):
        self.assertTrue(self.connection)

        with patch.object(requests, "post", self._patched_post()):
            with patch.object(requests, "put", self._patched_put()):
                attachment = self.env["ir.attachment"].create(
                    {
                        "name": "Test Attachment",
                        "datas": b"Test data",
                        "res_model": "res.partner",
                        "res_id": self.partner.id,
                    }
                )
        self.assertTrue(attachment.contentgrid_ids)
