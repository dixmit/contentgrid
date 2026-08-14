# Copyright 2025 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import json
from unittest.mock import patch

import jwt
import requests
from cryptography.hazmat.primitives.asymmetric import rsa
from freezegun import freeze_time

from odoo import fields
from odoo.tests.common import HttpCase, tagged
from odoo.tools import mute_logger

from .common import ContentgridCase


class TestContentgridEndpoint(ContentgridCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.endpoint = cls.env["contentgrid.endpoint"].create(
            {
                "name": "partners",
                "connection_id": cls.connection.id,
                "kind": "attachment",
                "content_type": "attachment",
                "attachment_model_field": "res_model",
                "attachment_res_id_field": "res_id",
                "attachment_data_field": "datas",
                "attachment_filename_field": "name",
            }
        )

    def test_url(self):
        url = self.endpoint.url
        self.assertEqual(url, "http://localhost:8069/contentgrid/partners")


@tagged("-at_install", "post_install")
class TestContentgridEndpointController(HttpCase, ContentgridCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.endpoint = cls.env["contentgrid.endpoint"].create(
            {
                "name": "partners",
                "connection_id": cls.connection.id,
                "kind": "attachment",
                "content_type": "attachment",
                "attachment_model_field": "res_model",
                "attachment_res_id_field": "res_id",
                "attachment_data_field": "datas",
                "attachment_filename_field": "name",
            }
        )

    def _generate_jwt(self):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        numbers = public_key.public_numbers()
        jwks = {
            "keys": [
                {
                    "kty": "RSA",
                    "use": "sig",
                    "alg": "RS256",
                    "kid": self.connection.key,  # any unique ID you choose
                    "n": base64.urlsafe_b64encode(
                        numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, "big")
                    )
                    .rstrip(b"=")
                    .decode("ascii"),
                    "e": base64.urlsafe_b64encode(
                        numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, "big")
                    )
                    .rstrip(b"=")
                    .decode("ascii"),
                }
            ]
        }
        token = jwt.encode(
            {
                "aud": "http://127.0.0.1:8069/contentgrid/partners",
            },
            private_key,
            algorithm="RS256",
            headers={"kid": self.connection.key},
        )
        return jwks, token

    def test_post_no_token(self):
        with mute_logger("odoo.addons.contentgrid.controllers.main"):
            response = self.url_open(
                "/contentgrid/attachment",
                data="{}",
                headers={
                    "Content-Type": "application/json",
                    "ContentGrid-Application-Id": "123",
                },
            )
        self.assertEqual(response.status_code, 403)

    def test_post_no_key(self):
        with mute_logger("odoo.addons.contentgrid.controllers.main"):
            response = self.url_open(
                "/contentgrid/partners",
                data="{}",
                headers={
                    "Content-Type": "application/json",
                    "ContentGrid-Signature": "123",
                },
            )
        self.assertEqual(response.status_code, 403)

    def test_post_wrong_key(self):
        with mute_logger("odoo.addons.contentgrid.controllers.main"):
            response = self.url_open(
                "/contentgrid/partners",
                data="{}",
                headers={
                    "Content-Type": "application/json",
                    "ContentGrid-Application-Id": f"{self.connection.key}2",
                    "ContentGrid-Signature": "non_existing",
                },
            )
        self.assertEqual(response.status_code, 403)

    def test_generate_signature_wrong_audience(self):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        numbers = public_key.public_numbers()
        jwks = {
            "keys": [
                {
                    "kty": "RSA",
                    "use": "sig",
                    "alg": "RS256",
                    "kid": self.connection.key,  # any unique ID you choose
                    "n": base64.urlsafe_b64encode(
                        numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, "big")
                    )
                    .rstrip(b"=")
                    .decode("ascii"),
                    "e": base64.urlsafe_b64encode(
                        numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, "big")
                    )
                    .rstrip(b"=")
                    .decode("ascii"),
                }
            ]
        }
        token = jwt.encode(
            {
                "aud": "http://other_url/contentgrid/partners",
            },
            private_key,
            algorithm="RS256",
            headers={"kid": self.connection.key},
        )
        with (
            patch.object(requests, "get", self._patched_get(json.dumps(jwks))),
            mute_logger("odoo.addons.contentgrid.controllers.main"),
        ):
            response = self.url_open(
                "/contentgrid/partners",
                data=json.dumps(
                    {
                        "trigger": "create",
                    }
                ),
                headers={
                    "Content-Type": "application/json",
                    "ContentGrid-Application-Id": self.connection.key,
                    "ContentGrid-Signature": token,
                },
            )
        self.assertEqual(response.status_code, 403)

    def test_generate_create(self):
        """
        Check that a create webhook does nothing (for attachment endpoints)
        """
        jwks, token = self._generate_jwt()
        with patch.object(requests, "get", self._patched_get(json.dumps(jwks))):
            response = self.url_open(
                "/contentgrid/partners",
                data=json.dumps(
                    {
                        "trigger": "create",
                    }
                ),
                headers={
                    "Content-Type": "application/json",
                    "ContentGrid-Application-Id": self.connection.key,
                    "ContentGrid-Signature": token,
                },
            )
        self.assertEqual(response.status_code, 200)
        # Nothing should happen

    def test_generate_update_and_delete(self):
        """
        We will do the following steps:
        - Create an attachment through an update webhook
        - Update the attachment through another update webhook (verify by write date)
        - Delete the attachment through a delete webhook
        """
        self.skipTest(
            "Skipping test because of ContentGrid API changes, needs to be updated"
        )
        jwks, token = self._generate_jwt()
        self.assertFalse(
            self.env["ir.attachment"].search(
                [("res_model", "=", "res.partner"), ("res_id", "=", self.partner.id)]
            )
        )
        with (
            patch.object(requests, "get", self._patched_get(json.dumps(jwks))),
            patch.object(requests, "post", self._patched_post()),
            patch.object(requests, "put", self._patched_put()),
            freeze_time("2024-01-01 12:00:00"),
        ):
            response = self.url_open(
                "/contentgrid/partners",
                data=json.dumps(
                    {
                        "trigger": "update",
                        "new": {
                            "id": "non_existing",
                            "res_model": "res.partner",
                            "res_id": self.partner.id,
                            "_links": {
                                "self": {"href": "http://example.com/attachments/1"}
                            },
                        },
                    }
                ),
                headers={
                    "Content-Type": "application/json",
                    "ContentGrid-Application-Id": self.connection.key,
                    "ContentGrid-Signature": token,
                },
            )
        self.assertEqual(response.status_code, 200)
        attachment = self.env["ir.attachment"].search(
            [("res_model", "=", "res.partner"), ("res_id", "=", self.partner.id)]
        )
        self.assertTrue(attachment)
        self.assertEqual(
            attachment.create_date, fields.Datetime.to_datetime("2024-01-01 12:00:00")
        )
        self.assertEqual(
            attachment.write_date, fields.Datetime.to_datetime("2024-01-01 12:00:00")
        )
        self.assertTrue(attachment.contentgrid_ids)
        with (
            patch.object(requests, "get", self._patched_get()),
            patch.object(requests, "post", self._patched_post()),
            patch.object(requests, "put", self._patched_put()),
            freeze_time("2025-01-01 12:00:00"),
        ):
            response = self.url_open(
                "/contentgrid/partners",
                data=json.dumps(
                    {
                        "trigger": "update",
                        "new": {
                            "id": "non_existing",
                            "res_model": "res.partner",
                            "res_id": self.partner.id,
                            "_links": {
                                "self": {"href": "http://example.com/attachments/1"}
                            },
                        },
                    }
                ),
                headers={
                    "Content-Type": "application/json",
                    "ContentGrid-Application-Id": self.connection.key,
                    "ContentGrid-Signature": token,
                },
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            attachment,
            self.env["ir.attachment"].search(
                [("res_model", "=", "res.partner"), ("res_id", "=", self.partner.id)]
            ),
        )
        self.assertEqual(
            attachment.create_date, fields.Datetime.to_datetime("2024-01-01 12:00:00")
        )
        self.assertEqual(
            attachment.write_date, fields.Datetime.to_datetime("2025-01-01 12:00:00")
        )
        with (
            patch.object(requests, "post", self._patched_post()),
            patch.object(requests, "put", self._patched_put()),
        ):
            response = self.url_open(
                "/contentgrid/partners",
                data=json.dumps(
                    {
                        "trigger": "delete",
                        "old": {
                            "id": "non_existing",
                            "res_model": "res.partner",
                            "res_id": self.partner.id,
                            "_links": {
                                "self": {"href": "http://example.com/attachments/1"}
                            },
                        },
                    }
                ),
                headers={
                    "Content-Type": "application/json",
                    "ContentGrid-Application-Id": self.connection.key,
                    "ContentGrid-Signature": token,
                },
            )
        attachment.invalidate_recordset()
        self.assertFalse(attachment.contentgrid_ids)
