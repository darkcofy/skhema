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


_INGEST_MODULES: dict[str, str] = {
    "concepts": "gnosis.ingest",
    "stakeholders": "gnosis.ingest_stakeholders",
    "glossary": "gnosis.ingest_glossary",
    "synonyms": "gnosis.ingest_synonyms",
    "behavior": "gnosis.ingest_behavior",
    "mappings": "gnosis.ingest_mappings",
    "formalization": "gnosis.ingest_formalization",
}


@app.command(
    name="interview-kit",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def interview_kit(ctx: typer.Context) -> None:
    """Generate a per-stakeholder interview kit from the current workspace."""
    _run_module("gnosis.interview_kit", list(ctx.args))


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def ingest(ctx: typer.Context) -> None:
    """Ingest LLM-extracted worksheet YAML into a workspace.

    Usage:
      gnosis ingest concepts --from <file> --session <id> --interviewer <name>
      gnosis ingest stakeholders --from <file> --session <id> --interviewer <name>
    """
    args = list(ctx.args)
    if not args:
        print(
            "Usage: gnosis ingest <artifact> --from <file> --session <id> --interviewer <name>\n"
            f"Available artifacts: {', '.join(sorted(_INGEST_MODULES))}",
            file=sys.stderr,
        )
        sys.exit(2)

    artifact = args[0]
    if artifact not in _INGEST_MODULES:
        print(
            f"Error: unknown artifact '{artifact}'. Available: {', '.join(sorted(_INGEST_MODULES))}",
            file=sys.stderr,
        )
        sys.exit(2)

    module = _INGEST_MODULES[artifact]
    _run_module(module, args[1:])


if __name__ == "__main__":
    app()
