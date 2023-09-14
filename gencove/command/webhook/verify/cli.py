"""Webhook signature verification shell command definition."""
import click

from gencove.logger import echo_error, echo_info

from .utils import is_valid_signature


@click.command("verify")
@click.argument("secret")
@click.argument("header")
@click.argument("payload")
# pylint: disable=too-many-arguments
def verify(
    secret,
    header,
    payload,
):
    """Verify webhook signature.

    `SECRET`: key to be used as a secret for hmac algorithm.

    `HEADER`: Gencove-Signature header content.

    `PAYLOAD`: JSON payload (i.e., the request’s body).
    """
    if is_valid_signature(secret, header, payload):
        echo_info("Webhook payload successfully verified.")
    else:
        echo_error("Could not verify webhook payload.")
        raise click.Abort()
