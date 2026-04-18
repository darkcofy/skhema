"""Generate artifacts from ontology workspace data.

Four MVP generators:
  1. engagement_brief — Markdown summary of scope, stakeholders, criteria
  2. draft_glossary — Markdown glossary from glossary-seeds.csv
  3. terminology_conflicts — Report from synonym-conflicts.md
  4. concept_map — PlantUML class diagram from candidate-concepts.yaml
"""
import argparse
import csv
import os
import subprocess
import sys

from gnosis.client import find_repo_root, detect_client, resolve_workspace
from gnosis.readiness import load_rules, evaluate_all


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------

def generate_engagement_brief(workspace_path: str, rules: dict) -> str:
    """Generate an engagement brief from scope files.

    Reads engagement.md, stakeholders.yaml, and success-criteria.md
    to produce a summary report.

    Returns the path to the generated file.
    """
    output_path = os.path.join(workspace_path, "generated", "reports", "engagement-brief.md")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Read engagement.md
    engagement_path = os.path.join(workspace_path, "00_scope", "engagement.md")
    engagement_content = ""
    if os.path.isfile(engagement_path):
        with open(engagement_path, "r") as f:
            engagement_content = f.read()

    # Read stakeholders.yaml using PyYAML.
    # Accepts either a top-level list or a top-level mapping with a 'stakeholders' key.
    import yaml
    stakeholders_path = os.path.join(workspace_path, "00_scope", "stakeholders.yaml")
    stakeholders: list[dict] = []
    if os.path.isfile(stakeholders_path):
        with open(stakeholders_path, "r") as f:
            data = yaml.safe_load(f)
        if isinstance(data, list):
            stakeholders = [d for d in data if isinstance(d, dict)]
        elif isinstance(data, dict):
            raw = data.get("stakeholders", [])
            if isinstance(raw, list):
                stakeholders = [d for d in raw if isinstance(d, dict)]

    # Read success-criteria.md (optional)
    criteria_path = os.path.join(workspace_path, "00_scope", "success-criteria.md")
    criteria_content = ""
    if os.path.isfile(criteria_path):
        with open(criteria_path, "r") as f:
            criteria_content = f.read()

    # Build the brief
    lines = []
    lines.append("# Engagement Brief")
    lines.append("")
    lines.append("*Auto-generated from ontology workspace scope files.*")
    lines.append("")

    lines.append("## Scope")
    lines.append("")
    lines.append(engagement_content.strip())
    lines.append("")

    lines.append("## Stakeholders")
    lines.append("")
    if stakeholders:
        lines.append("| Name | Role |")
        lines.append("|------|------|")
        for s in stakeholders:
            name = s.get("name", "?")
            role = s.get("role", "?")
            lines.append(f"| {name} | {role} |")
    else:
        lines.append("*No stakeholders defined yet.*")
    lines.append("")

    if criteria_content:
        lines.append("## Success Criteria")
        lines.append("")
        lines.append(criteria_content.strip())
        lines.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    return output_path


def generate_draft_glossary(workspace_path: str, rules: dict) -> str:
    """Generate a draft glossary from glossary-seeds.csv.

    Reads the CSV and produces a Markdown glossary document.

    Returns the path to the generated file.
    """
    output_path = os.path.join(workspace_path, "generated", "glossary", "draft-glossary.md")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    csv_path = os.path.join(workspace_path, "01_language", "glossary-seeds.csv")
    entries = []
    if os.path.isfile(csv_path):
        with open(csv_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if any(cell.strip() for cell in row.values()):
                    entries.append(row)

    lines = []
    lines.append("# Draft Glossary")
    lines.append("")
    lines.append("*Auto-generated from glossary-seeds.csv.*")
    lines.append("")

    if entries:
        # Sort by term name
        term_key = None
        for key in entries[0]:
            if key and key.strip().lower() == "term":
                term_key = key
                break
        if term_key:
            entries.sort(key=lambda e: e.get(term_key, "").lower())

        for entry in entries:
            term = entry.get(term_key or "term", "?").strip()
            definition = entry.get("definition", "").strip()
            source = entry.get("source", "").strip()
            lines.append(f"## {term}")
            lines.append("")
            if definition:
                lines.append(definition)
            else:
                lines.append("*No definition provided.*")
            if source:
                lines.append("")
                lines.append(f"**Source:** {source}")
            lines.append("")
    else:
        lines.append("*No glossary entries found.*")
        lines.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    return output_path


def generate_terminology_conflicts(workspace_path: str, rules: dict) -> str:
    """Generate a terminology conflict report from synonym-conflicts.md.

    Reads the markdown, extracts conflict entries, and produces a
    formatted report.

    Returns the path to the generated file.
    """
    output_path = os.path.join(workspace_path, "generated", "reports", "terminology-conflicts.md")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    conflicts_path = os.path.join(workspace_path, "01_language", "synonym-conflicts.md")
    conflicts_content = ""
    if os.path.isfile(conflicts_path):
        with open(conflicts_path, "r") as f:
            conflicts_content = f.read()

    lines = []
    lines.append("# Terminology Conflict Report")
    lines.append("")
    lines.append("*Auto-generated from synonym-conflicts.md.*")
    lines.append("")

    if conflicts_content.strip():
        lines.append(conflicts_content.strip())
    else:
        lines.append("*No conflicts documented yet.*")
    lines.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    return output_path


def generate_concept_map(workspace_path: str, rules: dict) -> str:
    """Generate a PlantUML concept map from candidate-concepts.yaml.

    Reads concept definitions and groups them by domain to produce
    a class diagram in PlantUML syntax.

    Returns the path to the generated .puml file.
    """
    output_path = os.path.join(workspace_path, "generated", "diagrams", "concept-map.puml")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    concepts_path = os.path.join(workspace_path, "02_concepts", "candidate-concepts.yaml")
    concepts: list[dict] = []
    if os.path.isfile(concepts_path):
        import yaml
        with open(concepts_path, "r") as f:
            data = yaml.safe_load(f)
        if isinstance(data, list):
            concepts = [d for d in data if isinstance(d, dict)]
        elif isinstance(data, dict):
            raw = data.get("concepts", [])
            if isinstance(raw, list):
                concepts = [d for d in raw if isinstance(d, dict)]

    # Group concepts by domain
    domains = {}
    for c in concepts:
        domain = c.get("domain", "unknown")
        if domain not in domains:
            domains[domain] = []
        domains[domain].append(c)

    lines = []
    lines.append("@startuml concept-map")
    lines.append("!theme plain")
    lines.append("hide empty members")
    lines.append("")

    for domain, domain_concepts in sorted(domains.items()):
        safe_domain = domain.replace(" ", "_").replace("-", "_")
        lines.append(f'package "{domain}" as {safe_domain} {{')
        for c in domain_concepts:
            name = c.get("name", "Unknown")
            safe_name = name.replace(" ", "_").replace("-", "_")
            desc = c.get("description", "")
            lines.append(f'  class "{name}" as {safe_name} {{')
            if desc:
                lines.append(f"    {desc}")
            lines.append("  }")
        lines.append("}")
        lines.append("")

    # Add relationships. `related_to` is preferably a YAML list, but a
    # comma-separated string is accepted for hand-written legacy files.
    for c in concepts:
        name = c.get("name", "Unknown")
        safe_name = name.replace(" ", "_").replace("-", "_")
        related = c.get("related_to")
        if not related:
            continue
        if isinstance(related, str):
            rels = [r.strip().strip('"') for r in related.split(",")]
        elif isinstance(related, list):
            rels = [str(r).strip() for r in related]
        else:
            rels = []
        for rel in rels:
            if rel:
                safe_rel = rel.replace(" ", "_").replace("-", "_")
                lines.append(f"{safe_name} -- {safe_rel}")

    lines.append("")
    lines.append("@enduml")
    lines.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    # Attempt to render via skhema
    _render_via_skhema(output_path, workspace_path)

    return output_path


def _render_via_skhema(puml_path: str, workspace_path: str) -> None:
    """Attempt to render a PlantUML file to SVG via skhema.

    Calls bin/skhema render <file> --output <svg>.
    Failures are silently ignored (rendering is best-effort).
    """
    svg_path = puml_path.replace(".puml", ".svg")

    # Find bin/skhema relative to workspace
    # workspace_path is clients/<name>/ontology
    # bin/skhema is at repo root
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(workspace_path)))
    skhema_bin = os.path.join(repo_root, "bin", "skhema")

    if not os.path.isfile(skhema_bin):
        return

    try:
        subprocess.run(
            [skhema_bin, "render", puml_path, "--output", svg_path],
            capture_output=True,
            timeout=30,
        )
    except (subprocess.SubprocessError, OSError):
        pass  # Best-effort rendering


# ---------------------------------------------------------------------------
# Generator registry
# ---------------------------------------------------------------------------

GENERATORS = {
    "engagement_brief": generate_engagement_brief,
    "draft_glossary": generate_draft_glossary,
    "terminology_conflict_report": generate_terminology_conflicts,
    "concept_map": generate_concept_map,
}


def list_available(rules: dict, workspace_path: str) -> list[tuple[str, str]]:
    """Return list of (artifact_key, state) for all artifacts that are READY."""
    statuses = evaluate_all(rules, workspace_path)
    available = []
    for key, status in statuses.items():
        if status.state == "READY":
            available.append((key, "READY"))
    return available


def main():
    parser = argparse.ArgumentParser(
        prog="gnosis generate",
        description="Generate artifacts from workspace data.",
    )
    parser.add_argument("artifact", nargs="?", default="available",
                        help="Artifact to generate, or 'available' to list ready artifacts")
    parser.add_argument("--client", help="Client name (auto-detected if only one)")
    parser.add_argument("--force", action="store_true",
                        help="Generate even if artifact is not READY")
    args = parser.parse_args()

    root = find_repo_root()
    client = detect_client(root, args.client)
    workspace_path = resolve_workspace(root, client)

    rules_path = os.path.join(root, "src", "gnosis", "rules", "artifacts.yaml")
    rules = load_rules(rules_path)

    if args.artifact == "available":
        available = list_available(rules, workspace_path)
        if not available:
            print("No artifacts are READY yet. Run 'gnosis status' to see what's needed.")
            return
        generated = []
        for key, state in available:
            rule = rules[key]
            name = rule.get("name", key)
            output_path = os.path.join(workspace_path, rule["output"])
            GENERATORS[key](workspace_path, output_path)
            generated.append(name)
            print(f"  Generated: {name} -> {rule['output']}")
            if rule.get("renders_via") == "skhema":
                _render_via_skhema(root, output_path)
        print(f"\n{len(generated)} artifact(s) generated.")
        return

    # Generate a specific artifact
    artifact_key = args.artifact
    if artifact_key not in GENERATORS:
        print(f"Error: unknown artifact '{artifact_key}'", file=sys.stderr)
        print(f"Available: {', '.join(GENERATORS.keys())}", file=sys.stderr)
        sys.exit(1)

    # Check readiness unless --force
    if not args.force:
        statuses = evaluate_all(rules, workspace_path)
        if artifact_key in statuses and statuses[artifact_key].state == "BLOCKED":
            print(f"Error: artifact '{artifact_key}' is BLOCKED. Use --force to override.", file=sys.stderr)
            for msg in statuses[artifact_key].missing:
                print(f"  {msg}", file=sys.stderr)
            sys.exit(1)

    generator = GENERATORS[artifact_key]
    output_path = generator(workspace_path, rules)
    print(f"Generated: {output_path}")


if __name__ == "__main__":
    main()
