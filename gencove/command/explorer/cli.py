"""Commands to be executed from command line."""
# pylint: disable=E0012,C0330,R0913
import click

# This package enables Click to default to a command if it is not specified.
from click_default_group import DefaultGroup
import sh
import shutil
import sys


@click.group(
    cls=DefaultGroup,
    default_if_no_args=True,
    default="default",
)
def explorer():
    """Gencove Explorer commands."""
    pass


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
    if shutil.which("explorer") is None:
        click.echo(
            "It doesn't seem like this command has been run from the Explorer "
            "ecosystem. Please try running it again from within Explorer.",
            err=True,
        )
        sys.exit(1)

    try:
        sh.explorer(
            *ctx.args,
            _in=sys.stdin,
            _out=sys.stdout,
            _err=sys.stderr,
        )
    except sh.ErrorReturnCode as e:
        sys.exit(e.exit_code)
