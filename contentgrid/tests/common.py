# Copyright 2025 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

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


class ContentgridCase(TransactionCase):
    CONFIGURATION_DATA = CONFIGURATION_DATA

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.openid_url = "https://example.com/openid"
        cls.contentgrid_base_url = "https://example.com/api"
        cls.request_id = 1
        cls.connection = cls.env["contentgrid.connection"].create(
            {
                "name": "Test Connection",
                "openid_url": cls.openid_url,
                "openid_client_id": "client_id",
                "openid_client_secret": "client_secret",
                "base_url": cls.contentgrid_base_url,
                "key": "test_key",
            }
        )
        cls.configuration = cls.env["contentgrid.configuration"].create(
            {
                "name": "Test Configuration",
                "model_id": cls.env.ref("base.model_res_partner").id,
                "connection_id": cls.connection.id,
                "active": True,
                "configuration_data": cls.CONFIGURATION_DATA,
            }
        )
        cls.env["ir.config_parameter"].set_param(
            "web.base.url", "http://localhost:8069"
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

    def _patched_get(self, content=None):
        def _get(url, *args, **kwargs):
            response = requests.Response()
            response.status_code = 200
            self.request_id += 1
            if content is not None:
                response._content = content.encode()
            else:
                response._content = f'{{"id": "{self.request_id}"}}'.encode()
            return response

        return _get

    def _patched_put(self):
        def _put(url, *args, **kwargs):
            response = requests.Response()
            response.status_code = 200
            self.request_id += 1
            response._content = f'{{"id": "{self.request_id}"}}'.encode()
            return response

        return _put
