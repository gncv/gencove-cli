"""Webhook validation related utilites."""
import hashlib
import hmac


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

    return (
        hmac.new(
            secret.encode("utf-8"),
            "{}.{}".format(timestamp[1], payload).encode("utf-8"),
            hashlib.sha512,
        ).hexdigest()
        == signature[1]
    )
