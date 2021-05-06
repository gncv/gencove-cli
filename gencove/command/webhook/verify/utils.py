"""Webhook validation related utilites."""
import hashlib
import hmac


# Copied from https://docs.gencove.com/main/?python#webhook-signatures
def calculate_signature(secret, timestamp, payload):
    """Calculates hmac signature with the given secret"""
    signature_message = "{}.{}".format(timestamp, payload).encode("utf-8")
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
    header_content = header.split(",")
    if len(header_content) != 2:
        return False

    timestamp = header_content[0].split("=")
    signature = header_content[1].split("=")
    if len(timestamp) != 2 or len(signature) != 2:
        return False

    if signature[0] != "v1":
        return False

    return calculate_signature(secret, timestamp[1], payload) == signature[1]
