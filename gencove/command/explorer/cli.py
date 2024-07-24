"""Commands to be executed from command line."""
import shutil
import subprocess  # nosec B404 (bandit subprocess import)
import sys

import click

# This package enables Click to default to a command if it is not specified.
from click_default_group import DefaultGroup


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
                result = subprocess.run(  # nosec B607 (start_process_with_partial_path)
                    ["explorer", "internal", "print-commands"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                formatter.write(result.stdout)
            except subprocess.CalledProcessError:
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
        subprocess.run(  # nosec B603 (execution of untrusted input)
            ["explorer"] + ctx.args,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
            check=True,
        )
    except subprocess.CalledProcessError as exception:
        sys.exit(exception.returncode)


explorer.add_command(instances)
explorer.add_command(data)
