"""Test webhook verify command."""

import hmac
import json
from datetime import datetime
from hashlib import sha512
from uuid import uuid4

from click.testing import CliRunner

from gencove.command.webhook.cli import verify


# Copied from back_api2/core/crypto.py#get_hmac
def get_hmac(secret_key, payload=None, digestmode=sha512, timestamp=None):
    """Generates hmac signature."""
    if payload is None:
        payload = ""

    if not timestamp:
        timestamp = int(datetime.utcnow().timestamp())

    return (
        timestamp,
        hmac.new(
            secret_key.encode("utf-8"),
            f"{timestamp}.{payload}".encode("utf-8"),
            digestmode,
        ).hexdigest(),
    )


INVALID_SECRET = "INVALID_SECRET"
VALID_SECRET = "VALID_SECRET"
VALID_PAYLOAD = json.dumps(
    [
        {
            "event_id": str(uuid4()),
            "event_type": "analysis_complete_v2",
            "timestamp": str(datetime.utcnow()),
            "payload": {
                "project": {"id": str(uuid4())},
                "samples": [
                    {
                        "id": str(uuid4()),
                        "client_id": str(uuid4()),
                        "last_status": {"status": "success"},
                    }
                ],
            },
        }
    ]
)
VALID_TIMESTAMP, VALID_SIGNATURE = get_hmac(VALID_SECRET, VALID_PAYLOAD)
VALID_HEADER = f"t={VALID_TIMESTAMP},v1={VALID_SIGNATURE}"

INVALID_PAYLOAD = "INVALID_PAYLOAD"
INVALID_HEADER_VERSION = f"t={VALID_TIMESTAMP},v2={VALID_SIGNATURE}"

INVALID_HEADER_FIELDS = f"t={VALID_TIMESTAMP}"
INVALID_HEADER_DATA = "t,v"
INVALID_HEADER_TIMESTAMP = f"t=INVALID_TIMESTAMP,v1={VALID_SIGNATURE}"
INVALID_HEADER_SIGNATURE = f"t={VALID_TIMESTAMP},v1=INVALID_SIGNATURE"


def test_verify__invalid_signature():
    """Test verify for all possible inputs of invalid signatures."""

    invalid_inputs = [
        # Test header version different from v1
        [
            VALID_SECRET,
            INVALID_HEADER_VERSION,
            VALID_PAYLOAD,
        ],
        # Test header invalid (missing fields)
        [
            VALID_SECRET,
            INVALID_HEADER_FIELDS,
            VALID_PAYLOAD,
        ],
        # Test header data (missing '=')
        [
            VALID_SECRET,
            INVALID_HEADER_DATA,
            VALID_PAYLOAD,
        ],
        # Test header invalid timestamp
        [
            VALID_SECRET,
            INVALID_HEADER_TIMESTAMP,
            VALID_PAYLOAD,
        ],
        # Test header invalid signature
        [
            VALID_SECRET,
            INVALID_HEADER_SIGNATURE,
            VALID_PAYLOAD,
        ],
        # Test invalid secret
        [
            INVALID_SECRET,
            VALID_HEADER,
            VALID_PAYLOAD,
        ],
        # Test invalid payload
        [
            VALID_SECRET,
            VALID_HEADER,
            INVALID_PAYLOAD,
        ],
    ]

    for args in invalid_inputs:
        runner = CliRunner()

        res = runner.invoke(
            verify,
            args,
        )

        assert res.exit_code == 1
        assert "ERROR" in res.output


def test_verify__valid_signature():
    """Test verify valid signature."""

    runner = CliRunner()

    res = runner.invoke(
        verify,
        [
            VALID_SECRET,
            VALID_HEADER,
            VALID_PAYLOAD,
        ],
    )

    assert res.exit_code == 0
