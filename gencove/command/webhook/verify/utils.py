"""Webhook validation related utilites."""
import hashlib
import hmac

import requests


# Copied from https://docs.gencove.com/main/?python#webhook-signatures
def calculate_signature(secret, timestamp, payload):
    """Calculates hmac signature with the given secret"""
    signature_message = f"{timestamp}.{payload}".encode("utf-8")
    return hmac.new(
        secret.encode("utf-8"), signature_message, hashlib.sha512
    ).hexdigest()


def is_valid_signature(secret, header, payload):
    """Test if provided signature is a valid.

    secret (str): key to be used as a secret for hmac algorithm.
    header (str): Gencove-Signature header content.
    payload (str): JSON payload (i.e., the request’s body).

    Returns:
        bool: True if is a valid signature, False if not
    """
    header = requests.utils.parse_dict_header(header)

    if "v1" not in header or "t" not in header:
        return False

    return calculate_signature(secret, header["t"], payload) == header["v1"]
