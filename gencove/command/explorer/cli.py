"""Commands to be executed from command line."""
import shutil
import sys

import click

# This package enables Click to default to a command if it is not specified.
from click_default_group import DefaultGroup

import sh


@click.group(
    cls=DefaultGroup,
    default_if_no_args=True,
    default="default",
)
def explorer():
    """Gencove Explorer commands."""


# # API-related Gencove CLI commands would be added like standard Click commands
# # in the CLI like in the example below
# @explorer.command()
# def test():
#     print("test")


# This method handles commands that have not been explicitly defined above
@explorer.command(
    hidden=True,
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.pass_context
def default(ctx):
    """Default command to execute"""
    if shutil.which("explorer") is None:
        click.echo(
            "It doesn't seem like this command has been run from the Explorer "
            "ecosystem. Please try running it again from within Explorer.",
            err=True,
        )
        sys.exit(1)

    try:
        sh.explorer(  # pylint: disable=E1101
            *ctx.args,
            _in=sys.stdin,
            _out=sys.stdout,
            _err=sys.stderr,
        )
    except sh.ErrorReturnCode as exception:
        sys.exit(exception.exit_code)  # pylint: disable=E1101
