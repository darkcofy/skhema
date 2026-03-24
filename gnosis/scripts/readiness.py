"""Readiness rules engine — evaluates artifact readiness from workspace files.

Loads rules from artifacts.yaml, checks file existence and content thresholds,
returns status (READY/PARTIAL/BLOCKED) per artifact.
"""
import os
import re
from dataclasses import dataclass, field

from scripts.parsers import (
    count_yaml_entries,
    count_csv_rows,
    count_md_entries,
    check_md_sections,
    count_md_checkboxes,
    is_template_only,
)


# Stages and their files (fixed sequence)
STAGE_FILES = {
    0: ["00_scope/engagement.md", "00_scope/stakeholders.yaml",
        "00_scope/source-systems.yaml", "00_scope/success-criteria.md"],
    1: ["01_language/glossary-seeds.csv", "01_language/stakeholder-terms.md",
        "01_language/synonym-conflicts.md", "01_language/open-questions.md"],
    2: ["02_concepts/candidate-concepts.yaml", "02_concepts/concept-definitions.md",
        "02_concepts/concept-examples.yaml", "02_concepts/domain-boundaries.md"],
    3: ["03_mappings/source-to-canonical.csv", "03_mappings/field-mappings.csv",
        "03_mappings/system-overlaps.md", "03_mappings/authority-notes.md"],
    4: ["04_behavior/lifecycle-states.yaml", "04_behavior/events.yaml",
        "04_behavior/business-rules.md", "04_behavior/edge-cases.md"],
    5: ["05_formalization/ontology.yaml", "05_formalization/properties.yaml",
        "05_formalization/enums.yaml", "05_formalization/review-notes.md"],
}


STAGE_NAMES = [
    "Setup",
    "Language Capture",
    "Concept Modeling",
    "System Mapping",
    "Behavior & Constraints",
    "Formalization",
]


@dataclass
class ArtifactStatus:
    """Status of a single artifact's readiness."""
    state: str  # "READY", "PARTIAL", "BLOCKED"
    missing: list[str] = field(default_factory=list)
    details: dict[str, str] = field(default_factory=dict)


def _safe_yaml_parse(path: str) -> dict:
    """Minimal YAML parser for artifacts.yaml. Handles the specific structure
    of our rules files without requiring PyYAML."""
    with open(path, "r") as f:
        content = f.read()

    result = {}
    current_artifact = None
    current_key = None
    current_file = None
    in_requires = False
    in_files = False
    in_optional = False

    for line in content.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())

        # Top-level 'artifacts:' key
        if indent == 0 and stripped == "artifacts:":
            continue

        # Artifact name (indent 2)
        if indent == 2 and stripped.endswith(":") and ":" not in stripped[:-1]:
            current_artifact = stripped[:-1]
            result[current_artifact] = {}
            in_requires = False
            in_optional = False
            in_files = False
            continue

        if current_artifact is None:
            continue

        art = result[current_artifact]

        # Simple key-value at artifact level (indent 4)
        if indent == 4:
            if stripped.startswith("name:"):
                art["name"] = stripped.split(":", 1)[1].strip().strip('"')
            elif stripped.startswith("stage:"):
                art["stage"] = int(stripped.split(":", 1)[1].strip())
            elif stripped.startswith("output:"):
                art["output"] = stripped.split(":", 1)[1].strip().strip('"')
            elif stripped.startswith("renders_via:"):
                art["renders_via"] = stripped.split(":", 1)[1].strip()
            elif stripped == "requires:":
                in_requires = True
                in_optional = False
                art["requires"] = {"files": []}
            elif stripped == "optional:":
                in_optional = True
                in_requires = False
                art["optional"] = []
            continue

        # Inside requires
        if in_requires:
            if indent == 6 and stripped == "files:":
                in_files = True
                continue
            if in_files:
                if indent == 8 and stripped.startswith("- path:"):
                    path_val = stripped.split(":", 1)[1].strip().strip('"')
                    current_file = {"path": path_val}
                    art["requires"]["files"].append(current_file)
                elif indent == 10 and current_file:
                    key, val = stripped.split(":", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("[]")
                    if key == "sections":
                        current_file["sections"] = [
                            s.strip().strip('"') for s in val.split(",")
                        ]
                    elif key in ("min_entries", "min_rows"):
                        current_file[key] = int(val)

        # Inside optional
        if in_optional:
            if stripped.startswith("- path:"):
                path_val = stripped.split(":", 1)[1].strip().strip('"')
                art["optional"].append({"path": path_val})

    return result


def load_rules(rules_path: str) -> dict:
    """Load artifact rules from YAML file."""
    return _safe_yaml_parse(rules_path)


def evaluate_artifact(rule: dict, workspace_path: str) -> ArtifactStatus:
    """Evaluate readiness of a single artifact against the workspace.

    Returns ArtifactStatus with state READY/PARTIAL/BLOCKED.
    """
    missing = []
    details = {}
    requirements_met = 0
    total_requirements = 0

    for file_req in rule.get("requires", {}).get("files", []):
        total_requirements += 1
        file_path = os.path.join(workspace_path, file_req["path"])

        if not os.path.isfile(file_path):
            missing.append(f"File missing: {file_req['path']}")
            continue

        # Check sections requirement (markdown)
        if "sections" in file_req:
            section_results = check_md_sections(file_path, file_req["sections"])
            missing_sections = [s for s, present in section_results.items() if not present]
            if missing_sections:
                missing.append(f"{file_req['path']}: missing sections {missing_sections}")
            else:
                requirements_met += 1
            continue

        # Check min_entries requirement (yaml or markdown)
        if "min_entries" in file_req:
            if file_req["path"].endswith(".yaml"):
                count = count_yaml_entries(file_path)
            else:
                count = count_md_entries(file_path)
            threshold = file_req["min_entries"]
            if count >= threshold:
                requirements_met += 1
            else:
                missing.append(f"{file_req['path']}: {count}/{threshold} entries")
                details[file_req["path"]] = f"{count}/{threshold}"
            continue

        # Check min_rows requirement (csv)
        if "min_rows" in file_req:
            count = count_csv_rows(file_path)
            threshold = file_req["min_rows"]
            if count >= threshold:
                requirements_met += 1
            else:
                missing.append(f"{file_req['path']}: {count}/{threshold} rows")
                details[file_req["path"]] = f"{count}/{threshold}"
            continue

        # File exists, no threshold — counts as met
        requirements_met += 1

    if total_requirements == 0:
        return ArtifactStatus(state="BLOCKED", missing=["No requirements defined"])

    if requirements_met == total_requirements:
        return ArtifactStatus(state="READY")
    elif requirements_met == 0:
        return ArtifactStatus(state="BLOCKED", missing=missing, details=details)
    else:
        return ArtifactStatus(state="PARTIAL", missing=missing, details=details)


def evaluate_all(rules: dict, workspace_path: str) -> dict[str, ArtifactStatus]:
    """Evaluate all artifacts and return a dict of artifact_key -> ArtifactStatus."""
    results = {}
    for key, rule in rules.items():
        results[key] = evaluate_artifact(rule, workspace_path)
    return results


def _file_completeness(file_path: str, rules: dict) -> float:
    """Compute completeness score for a single file (0.0 to 1.0).

    - Markdown: checked_criteria / total_criteria
    - YAML: min(actual / expected, 1.0) from rules
    - CSV: min(actual / expected, 1.0) from rules
    """
    if not os.path.isfile(file_path):
        return 0.0

    rel_path = None
    # Find this file's rule (if any)
    expected = None
    for artifact in rules.values():
        for file_req in artifact.get("requires", {}).get("files", []):
            # Match by filename
            if file_path.endswith(file_req["path"]):
                rel_path = file_req["path"]
                if "min_entries" in file_req:
                    expected = ("entries", file_req["min_entries"])
                elif "min_rows" in file_req:
                    expected = ("rows", file_req["min_rows"])
                break

    ext = os.path.splitext(file_path)[1]

    if ext == ".md":
        checked, total = count_md_checkboxes(file_path)
        if total > 0:
            return checked / total
        # No checkboxes — check if file was modified from template
        # Load template content for comparison (templates_dir resolved from gnosis root)
        gnosis_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        templates_dir = os.path.join(gnosis_root, "templates")
        # Find matching template by relative path within stage dirs
        for stage_files in STAGE_FILES.values():
            for sf in stage_files:
                if file_path.endswith(sf):
                    template_path = os.path.join(templates_dir, sf)
                    if os.path.isfile(template_path):
                        template_content = open(template_path).read()
                        return 0.0 if is_template_only(file_path, template_content) else 1.0
        return 0.0

    if ext == ".yaml":
        actual = count_yaml_entries(file_path)
        if expected and expected[0] == "entries":
            return min(actual / expected[1], 1.0) if expected[1] > 0 else (1.0 if actual > 0 else 0.0)
        return 1.0 if actual > 0 else 0.0

    if ext == ".csv":
        actual = count_csv_rows(file_path)
        if expected and expected[0] == "rows":
            return min(actual / expected[1], 1.0) if expected[1] > 0 else (1.0 if actual > 0 else 0.0)
        return 1.0 if actual > 0 else 0.0

    return 0.0


def compute_stage_completion(stage: int, rules: dict, workspace_path: str) -> int:
    """Compute stage completion as an integer percentage (0-100).

    Average of all file completeness scores in the stage.
    """
    files = STAGE_FILES.get(stage, [])
    if not files:
        return 0

    scores = []
    for rel_path in files:
        full_path = os.path.join(workspace_path, rel_path)
        scores.append(_file_completeness(full_path, rules))

    if not scores:
        return 0

    return round(sum(scores) / len(scores) * 100)
