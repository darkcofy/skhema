"""skhema CLI — Typer entry point."""
import os
import sys
from pathlib import Path

import typer

app = typer.Typer(
    name="skhema",
    help="skhema — architecture deliverable packager.",
    no_args_is_help=True,
    add_completion=False,
)


def _run_module(module: str, extra_args: list[str]) -> None:
    """Dispatch to a module's main() with the given CLI args."""
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
def render(ctx: typer.Context) -> None:
    """Render PlantUML diagrams."""
    _run_module("skhema.render", list(ctx.args))


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def gallery(ctx: typer.Context) -> None:
    """Generate self-contained HTML gallery."""
    _run_module("skhema.gallery", list(ctx.args))


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def docs(ctx: typer.Context) -> None:
    """Generate living architecture handbook."""
    _run_module("skhema.docs", list(ctx.args))


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def deck(ctx: typer.Context) -> None:
    """Export client diagrams as a deck."""
    _run_module("skhema.deck", list(ctx.args))


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def validate(ctx: typer.Context) -> None:
    """Lint diagrams for convention violations."""
    _run_module("skhema.validate", list(ctx.args))


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def adr(ctx: typer.Context) -> None:
    """Analyze architecture decision records."""
    _run_module("skhema.adr", list(ctx.args))


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def structurizr(ctx: typer.Context) -> None:
    """Export/validate/view Structurizr DSL workspaces."""
    _run_module("skhema.structurizr", list(ctx.args))


@app.command()
def init(name: str) -> None:
    """Scaffold a new client directory structure."""
    root = _find_repo_root()
    client_dir = root / "clients" / name
    if client_dir.exists():
        typer.echo(f"Client '{name}' already exists at {client_dir}", err=True)
        raise typer.Exit(1)

    display_name = " ".join(
        word.capitalize() for word in name.replace("-", " ").replace("_", " ").split()
    )

    for sub in ("diagrams/c4", "diagrams/sequence", "diagrams/erd", "diagrams/deployment", "models", "docs"):
        (client_dir / sub).mkdir(parents=True, exist_ok=True)

    (client_dir / "client.yaml").write_text(
        f'name: "{display_name}"\n'
        f'subtitle: "Architecture Documentation"\n'
        f'accent_color: "#D97706"\n'
        f'sections:\n'
        f'  - c4\n'
        f'  - sequence\n'
        f'  - erd\n'
        f'  - deployment\n'
    )
    (client_dir / "docs" / "overview.md").write_text(
        f"# {display_name}\n\n"
        f"*Add a brief description of the client and the scope of this architecture documentation.*\n"
    )
    typer.echo(f"Client '{name}' created at {client_dir}")


@app.command()
def serve(
    client: str = typer.Option(..., help="Client name"),
    port: int = typer.Option(8000, help="Port to serve on"),
    open_deck: bool = typer.Option(
        True, "--open-deck/--no-open-deck",
        help="Try to open the deck in your browser",
    ),
) -> None:
    """Serve a client's outputs over HTTP so Reveal.js presenter view works."""
    import http.server
    import socketserver
    import webbrowser

    root = _find_repo_root()
    client_dir = root / "clients" / client
    if not client_dir.is_dir():
        typer.echo(f"Client '{client}' not found at {client_dir}", err=True)
        raise typer.Exit(1)

    os.chdir(client_dir)
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        url = f"http://localhost:{port}/deck.html"
        typer.echo(f"Serving {client_dir} on port {port}")
        typer.echo(f"  Deck:     {url}")
        typer.echo(f"  Gallery:  http://localhost:{port}/index.html")
        typer.echo(f"  Handbook: http://localhost:{port}/{client}-architecture.html")
        typer.echo("\n  Press Ctrl+C to stop.\n")
        if open_deck:
            try:
                webbrowser.open(url)
            except Exception:
                pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            typer.echo("\nStopped.")


@app.command()
def demo(client: str = "demo") -> None:
    """Regenerate all outputs for a client."""
    for step, args in [
        ("Rendering diagrams", ["skhema.render", "--client", client, "--all", "--animate"]),
        ("Generating gallery", ["skhema.gallery", "--client", client, "--history", "0"]),
        ("Generating living docs", ["skhema.docs", "--client", client]),
        ("Generating deck", ["skhema.deck", "--client", client]),
    ]:
        typer.echo(f"\n=== {step} ===")
        _run_module(args[0], args[1:])
    typer.echo(f"\nDone. Outputs in clients/{client}/")


def _find_repo_root() -> Path:
    path = Path(__file__).resolve()
    for parent in path.parents:
        if (parent / "clients").is_dir():
            return parent
    return Path.cwd()


if __name__ == "__main__":
    app()
