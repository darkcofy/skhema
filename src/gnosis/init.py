"""Scaffold a new ontology workspace for a client.

Creates the client directory, client.yaml, and copies all stage templates
with variable substitution.
"""
import argparse
import os
import shutil
import sys
from datetime import date

from gnosis.client import find_repo_root


TEMPLATE_STAGES = [
    "00_scope",
    "01_language",
    "02_concepts",
    "03_mappings",
    "04_behavior",
    "05_formalization",
]


def scaffold_workspace(root: str, client_name: str, domain: str | None = None) -> str:
    """Create a new client with ontology workspace and template files.

    Args:
        root: Repository root path.
        client_name: Kebab-case client name (e.g. 'nova-pay').
        domain: Optional domain name for template substitution.

    Returns:
        Path to the created client directory.
    """
    client_dir = os.path.join(root, "clients", client_name)
    ontology_dir = os.path.join(client_dir, "ontology")

    if os.path.exists(client_dir):
        print(f"Error: client '{client_name}' already exists at {client_dir}", file=sys.stderr)
        sys.exit(1)

    # Convert kebab-case to Title Case for display name
    display_name = " ".join(
        word.capitalize() for word in client_name.replace("-", " ").replace("_", " ").split()
    )

    domain_value = domain or display_name

    # Create client.yaml
    os.makedirs(client_dir, exist_ok=True)
    client_yaml = os.path.join(client_dir, "client.yaml")
    with open(client_yaml, "w") as f:
        f.write(f'name: "{display_name}"\n')
        f.write(f'domain: "{domain_value}"\n')
        f.write('accent_color: "#D97706"\n')

    # Create ontology stage directories and copy templates
    gnosis_root = os.path.join(root, "src", "gnosis")
    templates_dir = os.path.join(gnosis_root, "templates")

    today = date.today().isoformat()

    # Copy workspace.yaml with substitution
    workspace_template = os.path.join(templates_dir, "workspace.yaml")
    os.makedirs(ontology_dir, exist_ok=True)
    if os.path.isfile(workspace_template):
        with open(workspace_template, "r") as f:
            content = f.read()
        content = content.replace("{{DOMAIN}}", domain_value)
        content = content.replace("{{DATE}}", today)
        with open(os.path.join(ontology_dir, "workspace.yaml"), "w") as f:
            f.write(content)

    # Copy stage template files
    for stage in TEMPLATE_STAGES:
        stage_src = os.path.join(templates_dir, stage)
        stage_dst = os.path.join(ontology_dir, stage)
        os.makedirs(stage_dst, exist_ok=True)

        if not os.path.isdir(stage_src):
            continue

        for filename in os.listdir(stage_src):
            src_file = os.path.join(stage_src, filename)
            dst_file = os.path.join(stage_dst, filename)
            if os.path.isfile(src_file):
                with open(src_file, "r") as f:
                    content = f.read()
                content = content.replace("{{DOMAIN}}", domain_value)
                content = content.replace("{{DATE}}", today)
                content = content.replace("{{CLIENT}}", display_name)
                with open(dst_file, "w") as f:
                    f.write(content)

    # Create generated output directories
    os.makedirs(os.path.join(ontology_dir, "generated", "reports"), exist_ok=True)
    os.makedirs(os.path.join(ontology_dir, "generated", "glossary"), exist_ok=True)
    os.makedirs(os.path.join(ontology_dir, "generated", "diagrams"), exist_ok=True)

    return client_dir


def main():
    parser = argparse.ArgumentParser(
        prog="gnosis init",
        description="Scaffold a new ontology workspace for a client.",
    )
    parser.add_argument("name", help="Client name (kebab-case, e.g. 'nova-pay')")
    parser.add_argument("--domain", help="Domain name for template substitution")
    args = parser.parse_args()

    root = find_repo_root()
    client_dir = scaffold_workspace(root, args.name, args.domain)

    print(f"Ontology workspace created at {client_dir}")
    print("")
    print("Next steps:")
    print(f"  1. Fill in clients/{args.name}/ontology/00_scope/engagement.md")
    print(f"  2. Check status:  gnosis status --client {args.name}")
    print(f"  3. Generate:      gnosis generate available --client {args.name}")


if __name__ == "__main__":
    main()
