"""Generate a per-stakeholder interview kit from the current gnosis workspace.

Deterministic — no LLM calls. Reads the workspace and rolls up:

  1. Open questions this stakeholder can answer (cited in concept source_quotes)
  2. Low-confidence concepts to firm up with this stakeholder
  3. Unresolved synonym conflicts where this stakeholder is on record
  4. TBD stakeholder placeholders (they may be able to make introductions)

Writes a markdown kit to `generated/interview-kits/<date>-<stakeholder>.md`
for the consultant to bring to the next session.

Usage:
    gnosis interview-kit --client meshco --stakeholder "Emma Ward"
    gnosis interview-kit --client meshco                  # all known stakeholders
"""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone

from gnosis.ingest import _normalise_name, load_concepts_yaml
from gnosis.ingest_stakeholders import StakeholderEntry, load_stakeholders_yaml


@dataclass
class InterviewKitSection:
    heading: str
    items: list[str] = field(default_factory=list)
    empty_note: str = ""


@dataclass
class InterviewKit:
    stakeholder: str
    sections: list[InterviewKitSection]
    generated_at: datetime
    output_path: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _stakeholder_cited_in_concept_quotes(stakeholder_name: str, concept) -> bool:
    target = _normalise_name(stakeholder_name)
    for sq in concept.source_quotes:
        if _normalise_name(sq.source) == target:
            return True
    return False


def _resolve_stakeholder(requested: str, all_stakeholders: list[StakeholderEntry]) -> StakeholderEntry | None:
    """Find a stakeholder by case-insensitive exact match or unique prefix.

    Returns None if no match or ambiguous. TBD placeholders are not selectable.
    """
    target = _normalise_name(requested)
    named = [s for s in all_stakeholders if s.name.strip().upper() != "TBD"]

    exact = [s for s in named if _normalise_name(s.name) == target]
    if len(exact) == 1:
        return exact[0]

    prefix = [s for s in named if _normalise_name(s.name).startswith(target)]
    if len(prefix) == 1:
        return prefix[0]

    return None


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _section_open_questions(workspace_path: str, stakeholder_name: str) -> InterviewKitSection:
    concepts_path = os.path.join(workspace_path, "02_concepts", "candidate-concepts.yaml")
    concepts = load_concepts_yaml(concepts_path) if os.path.isfile(concepts_path) else []
    section = InterviewKitSection(
        heading="Open questions from prior concept work",
        empty_note="No outstanding questions attributed to this stakeholder.",
    )
    for c in concepts:
        if not _stakeholder_cited_in_concept_quotes(stakeholder_name, c):
            continue
        for q in c.open_questions:
            section.items.append(f"**{c.name}:** {q}")
    return section


def _section_low_confidence_concepts(workspace_path: str, stakeholder_name: str) -> InterviewKitSection:
    concepts_path = os.path.join(workspace_path, "02_concepts", "candidate-concepts.yaml")
    concepts = load_concepts_yaml(concepts_path) if os.path.isfile(concepts_path) else []
    section = InterviewKitSection(
        heading="Low-confidence concepts to firm up",
        empty_note="No low-confidence concepts are attributed to this stakeholder.",
    )
    for c in concepts:
        if c.confidence != "low":
            continue
        if not _stakeholder_cited_in_concept_quotes(stakeholder_name, c):
            continue
        definition = c.description
        if len(definition) > 140:
            definition = definition[:137] + "..."
        section.items.append(f"**{c.name}** — {definition}")
    return section


def _section_unresolved_synonyms(workspace_path: str, stakeholder_name: str) -> InterviewKitSection:
    """Surface unresolved synonym-conflicts this stakeholder has a recorded usage in."""
    section = InterviewKitSection(
        heading="Unresolved terminology conflicts",
        empty_note="No unresolved synonym conflicts involve this stakeholder.",
    )
    yaml_path = os.path.join(workspace_path, "01_language", "synonym-conflicts.yaml")
    if not os.path.isfile(yaml_path):
        return section

    import yaml
    with open(yaml_path) as f:
        raw = yaml.safe_load(f) or []
    if not isinstance(raw, list):
        return section

    target = _normalise_name(stakeholder_name)

    for entry in raw:
        if not isinstance(entry, dict):
            continue
        if entry.get("proposed_canonical"):
            continue
        used_by = entry.get("used_by") or []
        speaker_match = False
        cited_terms: list[str] = []
        if isinstance(used_by, list):
            for u in used_by:
                if not isinstance(u, dict):
                    continue
                speakers = u.get("speakers") or []
                if not isinstance(speakers, list):
                    continue
                if any(isinstance(s, str) and _normalise_name(s) == target for s in speakers):
                    speaker_match = True
                    term = u.get("term")
                    if isinstance(term, str):
                        cited_terms.append(term)
        if not speaker_match:
            continue
        title = entry.get("title", "(untitled)")
        terms = entry.get("terms") or []
        items_hint = ", ".join(t for t in terms if isinstance(t, str))
        cited_hint = f" — you used: {', '.join(cited_terms)}" if cited_terms else ""
        section.items.append(f"**{title}** ({items_hint}){cited_hint}")
    return section


def _section_tbd_introductions(workspace_path: str) -> InterviewKitSection:
    section = InterviewKitSection(
        heading="TBD stakeholders who may need introductions",
        empty_note="No TBD placeholders in the stakeholder list — nothing to ask about.",
    )
    stakeholders_path = os.path.join(workspace_path, "00_scope", "stakeholders.yaml")
    if not os.path.isfile(stakeholders_path):
        return section
    try:
        stakeholders = load_stakeholders_yaml(stakeholders_path)
    except Exception:
        # Malformed file — don't crash the kit, just skip the section.
        return section
    for s in stakeholders:
        if s.name.strip().upper() != "TBD":
            continue
        role = s.role or "(role unknown)"
        team = f" / {s.team}" if s.team else ""
        note = s.notes or ""
        if note:
            first_line = note.strip().splitlines()[0]
            section.items.append(f"**{role}{team}** — {first_line}")
        else:
            section.items.append(f"**{role}{team}** — no notes recorded")
    return section


# ---------------------------------------------------------------------------
# Build + render + write
# ---------------------------------------------------------------------------

def build_kit(
    workspace_path: str, stakeholder_name: str, at: datetime | None = None
) -> InterviewKit:
    if at is None:
        at = datetime.now(timezone.utc)
    sections = [
        _section_open_questions(workspace_path, stakeholder_name),
        _section_low_confidence_concepts(workspace_path, stakeholder_name),
        _section_unresolved_synonyms(workspace_path, stakeholder_name),
        _section_tbd_introductions(workspace_path),
    ]
    date_stem = at.date().isoformat()
    slug = stakeholder_name.strip().lower().replace(" ", "-")
    output_path = os.path.join(
        workspace_path, "generated", "interview-kits", f"{date_stem}-{slug}.md"
    )
    return InterviewKit(
        stakeholder=stakeholder_name,
        sections=sections,
        generated_at=at,
        output_path=output_path,
    )


def render_kit(kit: InterviewKit) -> str:
    lines: list[str] = []
    lines.append(f"# Interview kit — {kit.stakeholder}")
    lines.append("")
    lines.append(f"*Auto-generated from the current gnosis workspace on {kit.generated_at.date().isoformat()}.*")
    lines.append("")
    lines.append("This kit is deterministic — it reflects workspace state at the moment of generation. Run `gnosis interview-kit` again before the next session to pick up any intervening ingests.")
    lines.append("")

    for section in kit.sections:
        lines.append(f"## {section.heading}")
        lines.append("")
        if section.items:
            for item in section.items:
                lines.append(f"- {item}")
        else:
            lines.append(f"*{section.empty_note}*")
        lines.append("")

    return "\n".join(lines)


def write_kit(kit: InterviewKit) -> str:
    os.makedirs(os.path.dirname(kit.output_path), exist_ok=True)
    with open(kit.output_path, "w") as f:
        f.write(render_kit(kit))
    return kit.output_path


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    from gnosis.client import find_repo_root, detect_client, resolve_workspace

    parser = argparse.ArgumentParser(
        prog="gnosis interview-kit",
        description="Generate a per-stakeholder interview kit from the current workspace.",
    )
    parser.add_argument("--client", help="Client name (auto-detected if only one).")
    parser.add_argument(
        "--stakeholder",
        help="Stakeholder name (case-insensitive; partial prefix OK if unique). Omit to generate for every named stakeholder.",
    )
    args = parser.parse_args()

    root = find_repo_root()
    client = detect_client(root, args.client)
    workspace_path = resolve_workspace(root, client)

    stakeholders_path = os.path.join(workspace_path, "00_scope", "stakeholders.yaml")
    if not os.path.isfile(stakeholders_path):
        print("Error: stakeholders.yaml not found — run `gnosis ingest stakeholders` first.", file=sys.stderr)
        sys.exit(1)

    all_stakeholders = load_stakeholders_yaml(stakeholders_path)
    named = [s for s in all_stakeholders if s.name.strip().upper() != "TBD"]

    targets: list[StakeholderEntry] = []
    if args.stakeholder:
        resolved = _resolve_stakeholder(args.stakeholder, all_stakeholders)
        if resolved is None:
            names = ", ".join(s.name for s in named) or "(none)"
            print(
                f"Error: no unique match for '{args.stakeholder}'. Available: {names}",
                file=sys.stderr,
            )
            sys.exit(1)
        targets = [resolved]
    else:
        if not named:
            print("Error: no named stakeholders in the workspace.", file=sys.stderr)
            sys.exit(1)
        targets = named

    at = datetime.now(timezone.utc)
    written: list[str] = []
    for s in targets:
        kit = build_kit(workspace_path, s.name, at=at)
        path = write_kit(kit)
        written.append(path)

    print(f"Generated {len(written)} interview kit(s):")
    for path in written:
        print(f"  {os.path.relpath(path, root)}")


if __name__ == "__main__":
    main()
