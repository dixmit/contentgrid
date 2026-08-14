# Copyright 2025 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from unittest.mock import patch

import requests

from odoo.addons.mail.tools.discuss import Store
from odoo.addons.website.tools import MockRequest

from .common import ContentgridCase

CONFIGURATION_DATA = """
archiveDocument:
    data:
        name: record.name
        checksum: record.checksum
        create_datetime: parse_date(record.create_date)
        create_date: parse_date(record.create_date.date())
        create_date_false: parse_date(False)
        create_date_null: parse_date("NOT A DATE")
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


class TestContentgrid(ContentgridCase):
    CONFIGURATION_DATA = CONFIGURATION_DATA

    def test_connection(self):
        self.skipTest(
            "Skipping test because of ContentGrid API changes, needs to be updated"
        )
        store = Store()
        self.partner._thread_to_store(store)
        self.assertFalse(store.get_result()["mail.thread"][0]["contentgrid"])
        self.assertFalse(self.partner.get_contentgrid_data())
        with (
            patch.object(requests, "post", self._patched_post()),
            patch.object(requests, "put", self._patched_put()),
        ):
            attachment = self.env["ir.attachment"].create(
                {
                    "name": "Test Attachment",
                    "datas": b"Test data",
                    "res_model": "res.partner",
                    "res_id": self.partner.id,
                }
            )
        store = Store()
        attachment._to_store(store)
        self.assertTrue(store.get_result()["ir.attachment"][0]["contentgrid"])
        self.assertTrue(attachment.contentgrid_ids)
        self.partner.invalidate_recordset()
        store = Store()
        self.partner._thread_to_store(store)
        self.assertTrue(store.get_result()["mail.thread"][0]["contentgrid"])
        with (
            patch.object(requests, "get", self._patched_get()),
            patch.object(requests, "post", self._patched_post()),
        ):
            data = self.partner.get_contentgrid_data()
            attachment_data = attachment.get_contentgrid_data()
        self.assertTrue(data)
        self.assertTrue(attachment_data)
        partner_records = self.partner.contentgrid_record_ids
        self.assertTrue(partner_records)
        # Now we should check that everything works if we add another attachment
        # No new record should be created for the partner
        with (
            patch.object(requests, "post", self._patched_post()),
            patch.object(requests, "put", self._patched_put()),
        ):
            attachment = self.env["ir.attachment"].create(
                {
                    "name": "Test Attachment",
                    "datas": b"Test data",
                    "res_model": "res.partner",
                    "res_id": self.partner.id,
                }
            )
        self.partner.invalidate_recordset()
        self.assertEqual(partner_records, self.partner.contentgrid_record_ids)

    def test_force_no_push(self):
        attachment = (
            self.env["ir.attachment"]
            .with_context(contentgrid_no_push=True)
            .create(
                {
                    "name": "Test Attachment",
                    "datas": b"Test data",
                    "res_model": "res.partner",
                    "res_id": self.partner.id,
                }
            )
        )
        self.assertFalse(attachment.contentgrid_ids)

    def test_no_push_no_record_on_attachment_reassignment(self):
        """
        Check that it will not be tested on creation if it has no record associated
        Will be pushed when assigned to a record
        """
        attachment = self.env["ir.attachment"].create(
            {
                "name": "Test Attachment",
                "datas": b"Test data",
            }
        )
        self.assertFalse(attachment.contentgrid_ids)
        with (
            patch.object(requests, "post", self._patched_post()),
            patch.object(requests, "put", self._patched_put()),
        ):
            attachment.write(
                {
                    "res_model": "res.partner",
                    "res_id": self.partner.id,
                }
            )
        self.assertTrue(attachment.contentgrid_ids)

    def test_manual_push(self):
        """Testing the manual push of an attachment"""
        attachment = (
            self.env["ir.attachment"]
            .with_context(contentgrid_no_push=True)
            .create(
                {
                    "name": "Test Attachment",
                    "datas": b"Test data",
                    "res_model": "res.partner",
                    "res_id": self.partner.id,
                }
            )
            .with_context(contentgrid_no_push=False)
        )
        self.assertFalse(attachment.contentgrid_ids)
        attachment._push_to_contentgrid(True)
        self.assertFalse(attachment.contentgrid_ids)
        self.configuration.allow_manual_send = True
        with (
            patch.object(requests, "post", self._patched_post()),
            patch.object(requests, "put", self._patched_put()),
        ):
            attachment._push_to_contentgrid(True)
        self.assertTrue(attachment.contentgrid_ids)

    def test_attachment_stream_origin(self):
        """Ensure that the original HTTP Stream retrieval still works"""
        with (
            patch.object(requests, "post", self._patched_post()),
            patch.object(requests, "put", self._patched_put()),
        ):
            attachment = self.env["ir.attachment"].create(
                {
                    "name": "Test Attachment",
                    "datas": b"Test data",
                    "res_model": "res.partner",
                    "res_id": self.partner.id,
                }
            )
        self.assertTrue(attachment.contentgrid_ids)
        self.assertFalse(attachment.contentgrid_connection_id)
        with MockRequest(attachment.env):
            stream = attachment.sudo()._to_http_stream()
        self.assertEqual(stream.mimetype, attachment.mimetype)

    def test_attachment_stream_contentgrid(self):
        """Testing the HTTP Stream retrieval from Contentgrid storage"""
        self.configuration.use_contentgrid_for_storage = True
        self.configuration.contentgrid_storage_model = "archiveDocument"
        self.configuration.contentgrid_storage_field = "datas"
        with (
            patch.object(requests, "post", self._patched_post()),
            patch.object(requests, "put", self._patched_put()),
        ):
            attachment = self.env["ir.attachment"].create(
                {
                    "name": "Test Attachment",
                    "datas": b"Test data",
                    "res_model": "res.partner",
                    "res_id": self.partner.id,
                }
            )
        self.assertTrue(attachment.contentgrid_ids)
        self.assertTrue(attachment.contentgrid_connection_id)
        with (
            patch.object(requests, "post", self._patched_post()),
            patch.object(requests, "get", self._patched_get(content="Test data")),
        ):
            stream = attachment.sudo()._to_http_stream()
            self.assertEqual(stream.data, b"Test data")

    def test_contentgrid_no_update(self):
        """
        On Contentgrid stored attachments, updates from Odoo should not be pushed
        """
        self.configuration.use_contentgrid_for_storage = True
        self.configuration.contentgrid_storage_model = "archiveDocument"
        self.configuration.contentgrid_storage_field = "datas"
        with (
            patch.object(requests, "post", self._patched_post()),
            patch.object(requests, "put", self._patched_put()),
        ):
            attachment = self.env["ir.attachment"].create(
                {
                    "name": "Test Attachment",
                    "datas": b"Test data",
                    "res_model": "res.partner",
                    "res_id": self.partner.id,
                }
            )
        attachment.datas = base64.b64encode(
            b"New data"
        )  # This should be ignored and not pushed
        with (
            patch.object(requests, "post", self._patched_post()),
            patch.object(requests, "get", self._patched_get(content="Test data")),
        ):
            stream = attachment.sudo()._to_http_stream()
            self.assertEqual(stream.data, b"Test data")
