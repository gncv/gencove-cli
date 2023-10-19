"""Commands to be executed from command line."""
# pylint: disable=E0012,C0330,R0913
import click
from click_default_group import DefaultGroup


@click.group(
    cls=DefaultGroup,
    default="default",
    default_if_no_args=True,
)
def explorer():
    """Gencove Explorer commands."""


@explorer.command(
    hidden=True,
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.pass_context
def default(ctx):
    print("default")
    print(ctx.args)
