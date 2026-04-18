"""Tests for the gnosis generate command — artifact generators."""
import os
import pytest

from gnosis.readiness import load_rules
from gnosis.generate import (
    generate_engagement_brief,
    generate_draft_glossary,
    generate_terminology_conflicts,
    generate_concept_map,
    list_available,
    GENERATORS,
)


@pytest.fixture
def rules_path():
    """Path to the real artifacts.yaml rules file."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src", "gnosis",
        "rules", "artifacts.yaml"
    )


@pytest.fixture
def workspace_full(tmp_path):
    """Workspace with enough data for all generators to run."""
    ws = tmp_path / "ontology"

    # Stage 0: Scope
    (ws / "00_scope").mkdir(parents=True)
    (ws / "00_scope" / "engagement.md").write_text(
        "# Engagement\n\n"
        "## domain\nPayments platform.\n\n"
        "## outcomes\nCanonical data model and shared glossary.\n\n"
        "## out_of_scope\nReporting and BI.\n"
    )
    (ws / "00_scope" / "stakeholders.yaml").write_text(
        "- name: Alice\n  role: Product Manager\n"
        "- name: Bob\n  role: Data Engineer\n"
        "- name: Carol\n  role: Domain Expert\n"
    )
    (ws / "00_scope" / "success-criteria.md").write_text(
        "## Criteria\n- Shared glossary adopted\n- Zero ambiguous terms\n"
    )

    # Stage 1: Language
    (ws / "01_language").mkdir(parents=True)
    (ws / "01_language" / "glossary-seeds.csv").write_text(
        "term,definition,source\n"
        "transaction,A financial exchange,payments team\n"
        "account,A customer record,CRM\n"
        "ledger,A record of transactions,finance\n"
        "settlement,Final transfer of funds,treasury\n"
        "merchant,A business that accepts payments,onboarding\n"
        "chargeback,A disputed transaction reversal,risk team\n"
    )
    (ws / "01_language" / "synonym-conflicts.md").write_text(
        "# Synonym Conflicts\n\n"
        "## Capture\n\n"
        "## Transaction vs Payment\n"
        "Teams use these interchangeably but they differ.\n\n"
        "## Account vs Customer\n"
        "CRM says customer, billing says account.\n\n"
        "## Merchant vs Vendor\n"
        "Onboarding uses merchant, procurement uses vendor.\n\n"
        "## Completion criteria\n"
        "- [ ] All conflicts resolved\n"
    )

    # Stage 2: Concepts
    (ws / "02_concepts").mkdir(parents=True)
    (ws / "02_concepts" / "candidate-concepts.yaml").write_text(
        '- name: Transaction\n  domain: payments\n  description: "A financial exchange between parties"\n'
        '- name: Account\n  domain: customers\n  description: "A customer identity record"\n'
        '- name: Merchant\n  domain: payments\n  description: "Business accepting payments"\n  related_to: "Transaction"\n'
        '- name: Settlement\n  domain: treasury\n  description: "Final fund transfer"\n'
        '- name: Ledger\n  domain: finance\n  description: "Record of transactions"\n  related_to: "Transaction, Settlement"\n'
    )
    (ws / "02_concepts" / "concept-definitions.md").write_text(
        "# Concept Definitions\n\n"
        "## Capture\n\n"
        "## Transaction\nA financial exchange between two parties.\n\n"
        "## Account\nA customer record in the system.\n\n"
        "## Merchant\nA business entity that accepts payments.\n\n"
        "## Completion criteria\n"
        "- [ ] All concepts defined\n"
    )

    # Generated dirs
    (ws / "generated" / "reports").mkdir(parents=True)
    (ws / "generated" / "glossary").mkdir(parents=True)
    (ws / "generated" / "diagrams").mkdir(parents=True)

    return ws


@pytest.fixture
def workspace_empty(tmp_path):
    """Workspace with directories but no content files."""
    ws = tmp_path / "ontology"
    for stage in ["00_scope", "01_language", "02_concepts"]:
        (ws / stage).mkdir(parents=True)
    (ws / "generated" / "reports").mkdir(parents=True)
    (ws / "generated" / "glossary").mkdir(parents=True)
    (ws / "generated" / "diagrams").mkdir(parents=True)
    return ws


class TestGeneratorRegistry:
    def test_has_four_generators(self):
        assert len(GENERATORS) == 4

    def test_generator_keys(self):
        assert "engagement_brief" in GENERATORS
        assert "draft_glossary" in GENERATORS
        assert "terminology_conflict_report" in GENERATORS
        assert "concept_map" in GENERATORS


class TestEngagementBrief:
    def test_generates_file(self, workspace_full, rules_path):
        rules = load_rules(rules_path)
        path = generate_engagement_brief(str(workspace_full), rules)
        assert os.path.isfile(path)

    def test_contains_scope(self, workspace_full, rules_path):
        rules = load_rules(rules_path)
        path = generate_engagement_brief(str(workspace_full), rules)
        content = open(path).read()
        assert "Payments platform" in content

    def test_contains_stakeholders_table(self, workspace_full, rules_path):
        rules = load_rules(rules_path)
        path = generate_engagement_brief(str(workspace_full), rules)
        content = open(path).read()
        assert "Alice" in content
        assert "Product Manager" in content
        assert "|" in content  # Table format

    def test_contains_success_criteria(self, workspace_full, rules_path):
        rules = load_rules(rules_path)
        path = generate_engagement_brief(str(workspace_full), rules)
        content = open(path).read()
        assert "Success Criteria" in content

    def test_empty_workspace(self, workspace_empty, rules_path):
        rules = load_rules(rules_path)
        path = generate_engagement_brief(str(workspace_empty), rules)
        assert os.path.isfile(path)
        content = open(path).read()
        assert "Engagement Brief" in content


class TestDraftGlossary:
    def test_generates_file(self, workspace_full, rules_path):
        rules = load_rules(rules_path)
        path = generate_draft_glossary(str(workspace_full), rules)
        assert os.path.isfile(path)

    def test_contains_terms(self, workspace_full, rules_path):
        rules = load_rules(rules_path)
        path = generate_draft_glossary(str(workspace_full), rules)
        content = open(path).read()
        assert "transaction" in content.lower()
        assert "account" in content.lower()

    def test_terms_sorted(self, workspace_full, rules_path):
        rules = load_rules(rules_path)
        path = generate_draft_glossary(str(workspace_full), rules)
        content = open(path).read()
        # account should come before transaction alphabetically
        assert content.index("## account") < content.index("## transaction")

    def test_contains_definitions(self, workspace_full, rules_path):
        rules = load_rules(rules_path)
        path = generate_draft_glossary(str(workspace_full), rules)
        content = open(path).read()
        assert "financial exchange" in content.lower()

    def test_empty_workspace(self, workspace_empty, rules_path):
        rules = load_rules(rules_path)
        path = generate_draft_glossary(str(workspace_empty), rules)
        content = open(path).read()
        assert "No glossary entries" in content


class TestTerminologyConflicts:
    def test_generates_file(self, workspace_full, rules_path):
        rules = load_rules(rules_path)
        path = generate_terminology_conflicts(str(workspace_full), rules)
        assert os.path.isfile(path)

    def test_contains_conflicts(self, workspace_full, rules_path):
        rules = load_rules(rules_path)
        path = generate_terminology_conflicts(str(workspace_full), rules)
        content = open(path).read()
        assert "Transaction vs Payment" in content

    def test_empty_workspace(self, workspace_empty, rules_path):
        rules = load_rules(rules_path)
        path = generate_terminology_conflicts(str(workspace_empty), rules)
        content = open(path).read()
        assert "No conflicts documented" in content


class TestConceptMap:
    def test_generates_puml_file(self, workspace_full, rules_path):
        rules = load_rules(rules_path)
        path = generate_concept_map(str(workspace_full), rules)
        assert os.path.isfile(path)
        assert path.endswith(".puml")

    def test_contains_startuml(self, workspace_full, rules_path):
        rules = load_rules(rules_path)
        path = generate_concept_map(str(workspace_full), rules)
        content = open(path).read()
        assert "@startuml" in content
        assert "@enduml" in content

    def test_contains_concepts(self, workspace_full, rules_path):
        rules = load_rules(rules_path)
        path = generate_concept_map(str(workspace_full), rules)
        content = open(path).read()
        assert "Transaction" in content
        assert "Account" in content

    def test_groups_by_domain(self, workspace_full, rules_path):
        rules = load_rules(rules_path)
        path = generate_concept_map(str(workspace_full), rules)
        content = open(path).read()
        assert 'package "payments"' in content
        assert 'package "customers"' in content

    def test_contains_relationships(self, workspace_full, rules_path):
        rules = load_rules(rules_path)
        path = generate_concept_map(str(workspace_full), rules)
        content = open(path).read()
        # Merchant related_to Transaction
        assert "Merchant" in content
        assert "--" in content

    def test_empty_workspace(self, workspace_empty, rules_path):
        rules = load_rules(rules_path)
        path = generate_concept_map(str(workspace_empty), rules)
        content = open(path).read()
        assert "@startuml" in content


class TestListAvailable:
    def test_ready_artifacts_listed(self, workspace_full, rules_path):
        rules = load_rules(rules_path)
        available = list_available(rules, str(workspace_full))
        keys = [k for k, _ in available]
        assert "engagement_brief" in keys

    def test_empty_workspace_none_ready(self, workspace_empty, rules_path):
        rules = load_rules(rules_path)
        available = list_available(rules, str(workspace_empty))
        assert len(available) == 0
