"""Commands to be executed from command line."""
import shutil
import sys

import click

# This package enables Click to default to a command if it is not specified.
from click_default_group import DefaultGroup

import sh

from .data.cli import data
from .instances.cli import instances


def explorer_cli_installed():
    """Function that checks if the Explorer CLI is installed and accessible on
    the current system"""
    return shutil.which("explorer") is not None


class CustomEpilogDefaultGroup(DefaultGroup):
    """Click group class that inherits functionality from DefaultGroup and adds
    a custom epilog to collect top-level Explorer CLI command help"""

    def format_epilog(self, ctx, formatter):
        """Adds an epilog to describe Explorer CLI commands"""
        if explorer_cli_installed():
            try:
                out = sh.explorer.internal(  # pylint: disable=E1101
                    "print-commands",
                )
                formatter.write(out)
            except sh.ErrorReturnCode:
                # Ignore errors to fail gracefully if installed version of
                # explorer CLI does not support `print-commands`
                pass


@click.group(
    cls=CustomEpilogDefaultGroup,
    default_if_no_args=False,
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
    add_help_option=False,
)
@click.pass_context
def default(ctx):
    """Default command to execute"""
    if not explorer_cli_installed():
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


explorer.add_command(instances)
explorer.add_command(data)
