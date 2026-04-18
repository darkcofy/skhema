"""Show stage completion and artifact readiness for a gnosis workspace.

Provides a dashboard view of how far each ontology stage has progressed
and which artifacts are ready to be generated.
"""
import argparse
import os

from gnosis.client import find_repo_root, detect_client, resolve_workspace
from gnosis.readiness import (
    load_rules,
    evaluate_all,
    compute_stage_completion,
    STAGE_NAMES,
    STAGE_FILES,
)


def compute_status(rules: dict, workspace_path: str) -> dict:
    """Compute the full status of a workspace.

    Returns a dict with:
        stages: list of {name, index, completion_pct}
        artifacts: dict of artifact_key -> ArtifactStatus
    """
    stages = []
    for i, name in enumerate(STAGE_NAMES):
        pct = compute_stage_completion(i, rules, workspace_path)
        stages.append({
            "name": name,
            "index": i,
            "completion_pct": pct,
        })

    artifacts = evaluate_all(rules, workspace_path)

    return {
        "stages": stages,
        "artifacts": artifacts,
    }


def format_status(status: dict, rules: dict) -> str:
    """Format status into a human-readable report string.

    Args:
        status: Output of compute_status().
        rules: Loaded artifact rules (for names/metadata).

    Returns:
        Formatted multi-line string.
    """
    lines = []
    lines.append("=== Stage Completion ===")
    lines.append("")

    for stage in status["stages"]:
        pct = stage["completion_pct"]
        bar_width = 20
        filled = round(pct / 100 * bar_width)
        bar = "#" * filled + "." * (bar_width - filled)
        lines.append(f"  Stage {stage['index']}: {stage['name']:<25s} [{bar}] {pct:>3d}%")

    lines.append("")
    lines.append("=== Artifact Readiness ===")
    lines.append("")

    for key, artifact_status in status["artifacts"].items():
        rule = rules.get(key, {})
        name = rule.get("name", key)
        state = artifact_status.state
        icon = {"READY": "+", "PARTIAL": "~", "BLOCKED": "-"}.get(state, "?")
        lines.append(f"  [{icon}] {name:<35s} {state}")
        if artifact_status.missing:
            for msg in artifact_status.missing:
                lines.append(f"        {msg}")

    return "\n".join(lines)


def validate_workspace(workspace_path: str) -> list[str]:
    """Run structural validation checks on the workspace.

    Returns a list of warning/error messages. Empty list means valid.
    """
    issues = []

    # Check workspace.yaml exists
    ws_yaml = os.path.join(workspace_path, "workspace.yaml")
    if not os.path.isfile(ws_yaml):
        issues.append("ERROR: workspace.yaml not found")

    # Check all stage directories exist
    for stage_files in STAGE_FILES.values():
        for rel_path in stage_files:
            stage_dir = os.path.dirname(rel_path)
            full_dir = os.path.join(workspace_path, stage_dir)
            if not os.path.isdir(full_dir):
                issues.append(f"WARN: stage directory missing: {stage_dir}")
                break  # Only warn once per stage dir

    # Check generated output directories
    gen_dir = os.path.join(workspace_path, "generated")
    if not os.path.isdir(gen_dir):
        issues.append("WARN: generated/ directory missing")
    else:
        for subdir in ["reports", "glossary", "diagrams"]:
            if not os.path.isdir(os.path.join(gen_dir, subdir)):
                issues.append(f"WARN: generated/{subdir}/ directory missing")

    return issues


def main():
    parser = argparse.ArgumentParser(
        prog="gnosis status",
        description="Show stage completion and artifact readiness.",
    )
    parser.add_argument("--client", help="Client name (auto-detected if only one)")
    parser.add_argument("--validate", action="store_true",
                        help="Run structural validation checks")
    args = parser.parse_args()

    root = find_repo_root()
    client = detect_client(root, args.client)
    workspace_path = resolve_workspace(root, client)

    rules_path = os.path.join(root, "src", "gnosis", "rules", "artifacts.yaml")
    rules = load_rules(rules_path)

    status = compute_status(rules, workspace_path)
    print(format_status(status, rules))

    if args.validate:
        print("")
        issues = validate_workspace(workspace_path)
        if issues:
            print("=== Validation ===")
            print("")
            for issue in issues:
                print(f"  {issue}")
        else:
            print("=== Validation: all checks passed ===")


if __name__ == "__main__":
    main()
