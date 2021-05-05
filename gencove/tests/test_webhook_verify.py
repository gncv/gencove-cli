"""Test webhook verify command."""

import io
import json
import sys
from uuid import uuid4

from click import echo
from click.testing import CliRunner

from gencove.command.webhook.cli import verify


invalid_secret = "invalid_secret"
valid_secret = (
    "d6c46e7eed0c11e063b9f77323c36a037462950628f39e5ec8bc74e083eec96b"
)
valid_payload = '[{"event_id": "d379a51e-c213-466a-ba90-dc7179d522e6", "event_type": "analysis_complete_v2", "timestamp": "2021-05-05T14:38:39.925680Z", "payload": {"project": {"id": "9832e5c9-80e8-4852-9517-7489d6be74a3"}, "samples": [{"id": "798a1101-bac1-40d8-9f11-51db2b856bc7", "client_id": "s1", "last_status": {"status": "failed qc"}}]}}]'
invalid_payload = "invalid_payload"
valid_header = "t=1620225520,v1=29f9c3e0db2adee586e9ed3ab149823df003f00d3e5d47168155e65f302407d4b78e56bec16c02b984b147c95e795e208dc63f48096e3b1b1e090815e1c5af84"
invalid_header_version = "t=1492774577,v2=5257a869e7ecebeda32affa62cdca3fa51cad7e77a0e56ff536d0ce8e108d8bd"

invalid_header_fields = "t=1492774577"
invalid_header_data = "t,v"
invalid_header_timestamp = "t=TIMESTAMP,v1=5257a869e7ecebeda32affa62cdca3fa51cad7e77a0e56ff536d0ce8e108d8bd"
invalid_header_signature = "t=1620225520,v1=SIGNATURE"


def test_verify__invalid_signature():
    """Test verify for all possible inputs of invalid signatures."""

    invalid_inputs = [
        # Test header version different from v1
        [
            valid_secret,
            invalid_header_version,
            valid_payload,
        ],
        # Test header invalid (missing fields)
        [
            valid_secret,
            invalid_header_fields,
            valid_payload,
        ],
        # Test header data (missing '=')
        [
            valid_secret,
            invalid_header_data,
            valid_payload,
        ],
        # Test header invalid timestamp
        [
            valid_secret,
            invalid_header_timestamp,
            valid_payload,
        ],
        # Test header invalid signature
        [
            valid_secret,
            invalid_header_signature,
            valid_payload,
        ],
        # Test invalid secret
        [
            invalid_secret,
            valid_header,
            valid_payload,
        ],
        # Test invalid payload
        [
            valid_secret,
            valid_header,
            valid_payload,
        ],
    ]

    for args in invalid_inputs:
        runner = CliRunner()

        res = runner.invoke(
            verify,
            args,
        )

        assert res.exit_code == 0
        assert "INVALID" in res.output


def test_verify__valid_signature():
    runner = CliRunner()

    res = runner.invoke(
        verify,
        [
            valid_secret,
            valid_header,
            valid_payload,
        ],
    )

    assert res.exit_code == 0
    assert "OK" in res.output
