"""gnosis CLI — Typer entry point."""
import sys

import typer

app = typer.Typer(
    name="gnosis",
    help="gnosis — guided domain-discovery workflow.",
    no_args_is_help=True,
    add_completion=False,
)


def _run_module(module: str, extra_args: list[str]) -> None:
    old_argv = sys.argv
    sys.argv = [module, *extra_args]
    try:
        mod = __import__(module, fromlist=["main"])
        mod.main()
    finally:
        sys.argv = old_argv


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def init(ctx: typer.Context) -> None:
    """Scaffold a new ontology workspace for a client."""
    _run_module("gnosis.init", list(ctx.args))


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def status(ctx: typer.Context) -> None:
    """Show stage completion and artifact readiness."""
    _run_module("gnosis.status", list(ctx.args))


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def generate(ctx: typer.Context) -> None:
    """Generate artifacts from workspace data."""
    _run_module("gnosis.generate", list(ctx.args))


if __name__ == "__main__":
    app()
