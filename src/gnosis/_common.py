"""Shared helpers for the gnosis ingest modules.

Every `gnosis.ingest_*` module follows the same shape:
  1. Load fixture (YAML or CSV) and validate against a schema
  2. Load existing workspace state
  3. Run lint rules
  4. Merge new into existing with per-entry `last_ingested` provenance
  5. Write target file(s) + regenerate `ontology/ingest-warnings.md`
  6. Expose a `main()` CLI entry point that unifies args, error handling, and summary output

This module holds the bits that are genuinely reusable across those steps — the
provenance stamp, a YAML writer with the standard kwargs, fixture-path
resolution, and a CLI wrapper. Per-artifact schemas, lint rules, and merge
bodies stay in their owning modules.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from typing import Any, Callable


def make_provenance(session: str, interviewer: str, at: datetime) -> dict:
    """Build the `last_ingested` provenance block stamped onto every merged entry.

    ISO-format UTC timestamp, microseconds stripped for readable YAML.
    """
    return {
        "session": session,
        "interviewer": interviewer,
        "at": at.replace(microsecond=0).isoformat(),
    }


def write_yaml_list(payload: list[dict], path: str) -> None:
    """Serialise a list of dicts to YAML with the standard ingest kwargs.

    Block style, stable key order (as authored), UTF-8, wide wrap, parent dir
    created if missing. Matches the convention used by every ingest writer.
    """
    import yaml

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        yaml.safe_dump(
            payload,
            f,
            sort_keys=False,
            allow_unicode=True,
            width=100,
            default_flow_style=False,
        )


def resolve_fixture_path(source: str, root: str) -> str:
    """Resolve an ingest `--from` argument to an absolute path.

    Accepts absolute paths as-is. Relative paths are first tried against the
    repo root (so users can pass `clients/<name>/transcripts/_drafts/...` from
    anywhere); if that doesn't resolve, the original string is returned and
    the downstream `os.path.isfile` check surfaces the error.
    """
    if os.path.isabs(source):
        return source
    repo_rel = os.path.join(root, source)
    if os.path.isfile(repo_rel):
        return repo_rel
    return source


def run_ingest_cli(
    prog: str,
    description: str,
    source_help: str,
    ingest_fn: Callable[..., Any],
    print_summary: Callable[[Any, str], None],
    schema_error_header: str = "Ingest refused — schema errors in source:",
) -> None:
    """Common CLI harness for a `gnosis ingest <artifact>` module.

    Builds a parser with the four standard flags (--from / --client / --session
    / --interviewer), resolves the client workspace, invokes `ingest_fn`, and
    dispatches SchemaError/FileNotFoundError to sensible exit codes.

    `print_summary(result, root)` renders the human-readable outcome; each
    artifact has its own shape so the caller supplies this.
    """
    # Local imports — avoid a circular edge via gnosis.ingest at module load.
    from gnosis.client import find_repo_root, detect_client, resolve_workspace
    from gnosis.ingest import SchemaError

    parser = argparse.ArgumentParser(prog=prog, description=description)
    parser.add_argument("--from", dest="source", required=True, help=source_help)
    parser.add_argument("--client", help="Client name (auto-detected if only one).")
    parser.add_argument("--session", required=True, help="Session identifier for provenance.")
    parser.add_argument("--interviewer", required=True, help="Who ran the extraction.")
    args = parser.parse_args()

    root = find_repo_root()
    client = detect_client(root, args.client)
    workspace_path = resolve_workspace(root, client)

    source_path = resolve_fixture_path(args.source, root)

    try:
        result = ingest_fn(
            workspace_path=workspace_path,
            fixture_path=source_path,
            session=args.session,
            interviewer=args.interviewer,
        )
    except SchemaError as e:
        print(schema_error_header, file=sys.stderr)
        for issue in e.issues:
            print(f"  - {issue}", file=sys.stderr)
        print("", file=sys.stderr)
        print("No changes written. Fix the source file and re-run.", file=sys.stderr)
        sys.exit(2)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print_summary(result, root)
