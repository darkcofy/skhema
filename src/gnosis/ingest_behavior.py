"""Ingest LLM-extracted lifecycles + events into 04_behavior/{lifecycle-states,events}.yaml.

Matches the output format of `skills/gnosis/extracting-events-and-lifecycles.md`.
Accepts a single combined YAML with `lifecycles:` and/or `events:` top-level keys,
since the skill produces both at once and they cross-reference (transition triggers
reference event names).

BYOLLM — input is YAML the user has in their hands.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from gnosis._common import make_provenance, run_ingest_cli, write_yaml_list
from gnosis.ingest import (
    LintWarning,
    SchemaError,
    _normalise_name,
    load_concepts_yaml,
    load_stakeholder_names,
    write_warnings_file,
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

@dataclass
class SourceQuote:
    quote: str
    source: str
    date: str


@dataclass
class StateDef:
    name: str
    description: str


@dataclass
class TransitionDef:
    from_state: str
    to_state: str
    trigger: str


@dataclass
class LifecycleEntry:
    entity: str
    states: list[StateDef]
    transitions: list[TransitionDef]
    invariants: list[str] = field(default_factory=list)
    source_quotes: list[SourceQuote] = field(default_factory=list)
    last_ingested: dict | None = None


@dataclass
class EventEntry:
    name: str
    domain: str
    entity: str
    triggered_by: str
    carries: list[str]
    consumed_by: list[str] = field(default_factory=list)
    source_quotes: list[SourceQuote] = field(default_factory=list)
    last_ingested: dict | None = None


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _coerce_str_list(value, label: str, issues: list[str], required: bool = False) -> list[str]:
    if value is None:
        if required:
            issues.append(f"{label}: required and must be a non-empty list of strings")
            return []
        return []
    if not isinstance(value, list):
        issues.append(f"{label}: must be a list of strings")
        return []
    out: list[str] = []
    for v in value:
        if not isinstance(v, str) or not v.strip():
            issues.append(f"{label}: entries must be non-empty strings")
        else:
            out.append(v.strip())
    if required and not out:
        issues.append(f"{label}: must contain at least one entry")
    return out


def _parse_source_quotes(raw, label: str, issues: list[str]) -> list[SourceQuote]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        issues.append(f"{label}: must be a list")
        return []
    quotes: list[SourceQuote] = []
    for j, sq in enumerate(raw):
        sq_label = f"{label}[{j}]"
        if not isinstance(sq, dict):
            issues.append(f"{sq_label}: must be a mapping")
            continue
        q = sq.get("quote")
        s = sq.get("source")
        d = sq.get("date")
        if not isinstance(q, str) or not q.strip():
            issues.append(f"{sq_label}: 'quote' is required")
        if not isinstance(s, str) or not s.strip():
            issues.append(f"{sq_label}: 'source' is required")
        if isinstance(d, str) and re.match(r"^\d{4}-\d{2}-\d{2}$", d.strip()):
            d_str = d.strip()
        elif hasattr(d, "isoformat"):
            d_str = d.isoformat()
        else:
            issues.append(f"{sq_label}: 'date' is required (YYYY-MM-DD)")
            continue
        if isinstance(q, str) and isinstance(s, str):
            quotes.append(SourceQuote(quote=q.strip(), source=s.strip(), date=d_str))
    return quotes


# ---------------------------------------------------------------------------
# Lifecycle parsing
# ---------------------------------------------------------------------------

def parse_lifecycles(raw: list) -> list[LifecycleEntry]:
    if not isinstance(raw, list):
        raise SchemaError(["'lifecycles' must be a list"])

    issues: list[str] = []
    out: list[LifecycleEntry] = []
    seen: set[str] = set()

    for i, item in enumerate(raw):
        label = f"lifecycle[{i}]"
        if not isinstance(item, dict):
            issues.append(f"{label}: must be a mapping")
            continue

        entity = item.get("entity")
        if entity:
            label = f"lifecycle for '{entity}'"
        local: list[str] = []

        if not isinstance(entity, str) or not entity.strip():
            local.append(f"{label}: 'entity' is required")
        elif not re.match(r"^[A-Z][A-Za-z0-9]*$", entity.strip()):
            local.append(f"{label}: 'entity' must be PascalCase matching a concept name")
        else:
            key = entity.strip().casefold()
            if key in seen:
                local.append(f"{label}: duplicate lifecycle for entity '{entity}' in the same ingest")
            seen.add(key)

        # States
        states_raw = item.get("states")
        states: list[StateDef] = []
        if not isinstance(states_raw, list) or len(states_raw) < 2:
            local.append(f"{label}: 'states' must be a list of at least 2 entries")
        else:
            for j, s in enumerate(states_raw):
                s_label = f"{label} states[{j}]"
                if not isinstance(s, dict):
                    local.append(f"{s_label}: must be a mapping")
                    continue
                n = s.get("name")
                d = s.get("description")
                if not isinstance(n, str) or not re.match(r"^[a-z][a-z0-9_]*$", n.strip() if isinstance(n, str) else ""):
                    local.append(f"{s_label}: 'name' is required and must be snake_case")
                if not isinstance(d, str) or not d.strip():
                    local.append(f"{s_label}: 'description' is required")
                if isinstance(n, str) and isinstance(d, str):
                    states.append(StateDef(name=n.strip(), description=d.strip()))

        state_names = {s.name for s in states}

        # Transitions
        transitions_raw = item.get("transitions")
        transitions: list[TransitionDef] = []
        if not isinstance(transitions_raw, list) or len(transitions_raw) < 1:
            local.append(f"{label}: 'transitions' must be a list of at least 1 entry")
        else:
            for j, t in enumerate(transitions_raw):
                t_label = f"{label} transitions[{j}]"
                if not isinstance(t, dict):
                    local.append(f"{t_label}: must be a mapping")
                    continue
                fs = t.get("from")
                ts = t.get("to")
                tr = t.get("trigger")
                if not isinstance(fs, str) or not fs.strip():
                    local.append(f"{t_label}: 'from' is required")
                elif state_names and fs.strip() not in state_names:
                    local.append(f"{t_label}: 'from' state '{fs}' is not in states")
                if not isinstance(ts, str) or not ts.strip():
                    local.append(f"{t_label}: 'to' is required")
                elif state_names and ts.strip() not in state_names:
                    local.append(f"{t_label}: 'to' state '{ts}' is not in states")
                if not isinstance(tr, str) or not tr.strip():
                    local.append(f"{t_label}: 'trigger' is required")
                if (isinstance(fs, str) and isinstance(ts, str) and isinstance(tr, str)):
                    transitions.append(TransitionDef(from_state=fs.strip(), to_state=ts.strip(), trigger=tr.strip()))

        invariants = _coerce_str_list(item.get("invariants"), f"{label} invariants", local)
        quotes = _parse_source_quotes(item.get("source_quotes"), f"{label} source_quotes", local)

        if local:
            issues.extend(local)
            continue

        out.append(LifecycleEntry(
            entity=entity.strip(),
            states=states,
            transitions=transitions,
            invariants=invariants,
            source_quotes=quotes,
            last_ingested=item.get("last_ingested"),
        ))

    if issues:
        raise SchemaError(issues)

    return out


# ---------------------------------------------------------------------------
# Event parsing
# ---------------------------------------------------------------------------

def parse_events(raw: list) -> list[EventEntry]:
    if not isinstance(raw, list):
        raise SchemaError(["'events' must be a list"])

    issues: list[str] = []
    out: list[EventEntry] = []
    seen: set[str] = set()

    for i, item in enumerate(raw):
        label = f"event[{i}]"
        if not isinstance(item, dict):
            issues.append(f"{label}: must be a mapping")
            continue

        name = item.get("name")
        if name:
            label = f"event '{name}'"
        local: list[str] = []

        if not isinstance(name, str) or not name.strip():
            local.append(f"{label}: 'name' is required")
        elif not re.match(r"^[A-Z][A-Za-z0-9]*$", name.strip()):
            local.append(f"{label}: 'name' must be PascalCase (SubjectVerbed form)")
        else:
            key = name.strip().casefold()
            if key in seen:
                local.append(f"{label}: duplicate event '{name}' in the same ingest")
            seen.add(key)

        domain = item.get("domain")
        if not isinstance(domain, str) or not domain.strip():
            local.append(f"{label}: 'domain' is required")

        entity = item.get("entity")
        if not isinstance(entity, str) or not entity.strip():
            local.append(f"{label}: 'entity' is required")
        elif not re.match(r"^[A-Z][A-Za-z0-9]*$", entity.strip()):
            local.append(f"{label}: 'entity' must be PascalCase matching a concept name")

        triggered_by = item.get("triggered_by")
        if not isinstance(triggered_by, str) or not triggered_by.strip():
            local.append(f"{label}: 'triggered_by' is required")

        carries = _coerce_str_list(item.get("carries"), f"{label} carries", local, required=True)
        consumed_by = _coerce_str_list(item.get("consumed_by"), f"{label} consumed_by", local)
        quotes = _parse_source_quotes(item.get("source_quotes"), f"{label} source_quotes", local)

        if local:
            issues.extend(local)
            continue

        out.append(EventEntry(
            name=name.strip(),
            domain=domain.strip(),
            entity=entity.strip(),
            triggered_by=triggered_by.strip(),
            carries=carries,
            consumed_by=consumed_by,
            source_quotes=quotes,
            last_ingested=item.get("last_ingested"),
        ))

    if issues:
        raise SchemaError(issues)

    return out


# ---------------------------------------------------------------------------
# File loaders for existing state
# ---------------------------------------------------------------------------

def load_lifecycles_yaml(path: str) -> list[LifecycleEntry]:
    if not os.path.isfile(path):
        return []
    import yaml
    with open(path) as f:
        raw = yaml.safe_load(f) or []
    if isinstance(raw, dict):
        raw = raw.get("lifecycles", [])
    return parse_lifecycles(raw)


def load_events_yaml(path: str) -> list[EventEntry]:
    if not os.path.isfile(path):
        return []
    import yaml
    with open(path) as f:
        raw = yaml.safe_load(f) or []
    if isinstance(raw, dict):
        raw = raw.get("events", [])
    return parse_events(raw)


# ---------------------------------------------------------------------------
# Lint rules
# ---------------------------------------------------------------------------

_PAST_TENSE_SUFFIX_PATTERN = re.compile(r"(ed|en|ied|lt|nt|wn|one|ung|ought|aught|ade|ent|ost|ound)$", re.IGNORECASE)

_PAST_TENSE_WHITELIST = {
    "Sent", "Put", "Set", "Hit", "Cut", "Shut", "Let", "Read", "Led",
    "Lost", "Won", "Paid", "Made", "Held", "Found", "Bought", "Sold",
    "Built", "Broken", "Written", "Driven", "Taken", "Given",
    "Removed", "Added", "Updated", "Deleted", "Created", "Published",
    "Deprecated", "Retired", "Detected",
}


def _is_past_tense(event_name: str) -> bool:
    """Heuristic: True if event_name ends in a past-tense verb form.

    Split the PascalCase name into words and check the last one (the verb in
    SubjectVerbed form). A verb is past-tense if it ends in a common past-tense
    suffix OR is in the whitelist of irregulars.
    """
    # Split on capital letters: OrderPlaced -> ["Order", "Placed"]
    parts = re.findall(r"[A-Z][a-z0-9]*", event_name)
    if not parts:
        return False
    verb = parts[-1]
    if verb in _PAST_TENSE_WHITELIST:
        return True
    if _PAST_TENSE_SUFFIX_PATTERN.search(verb):
        return True
    return False


def lint_event_not_past_tense(events: list[EventEntry]) -> list[LintWarning]:
    """Flag events whose name doesn't look like SubjectVerbed past tense."""
    warnings: list[LintWarning] = []
    for e in events:
        if not _is_past_tense(e.name):
            warnings.append(
                LintWarning(
                    rule="event_not_past_tense",
                    concept=e.name,
                    message=(
                        "event name doesn't look past-tense — events describe things "
                        "that have happened (TransactionAuthorised, not AuthoriseTransaction)"
                    ),
                )
            )
    return warnings


def lint_unknown_entity(
    lifecycles: list[LifecycleEntry],
    events: list[EventEntry],
    known_concepts: set[str],
) -> list[LintWarning]:
    """Flag lifecycle entities and event entities that don't match a known concept."""
    warnings: list[LintWarning] = []
    concept_fold = {c.casefold() for c in known_concepts}
    for lc in lifecycles:
        if lc.entity.casefold() not in concept_fold:
            warnings.append(
                LintWarning(
                    rule="unknown_entity",
                    concept=f"lifecycle {lc.entity}",
                    message=(
                        f"entity '{lc.entity}' is not in 02_concepts/candidate-concepts.yaml — "
                        "add the concept first or rename to match an existing one"
                    ),
                )
            )
    for ev in events:
        if ev.entity.casefold() not in concept_fold:
            warnings.append(
                LintWarning(
                    rule="unknown_entity",
                    concept=f"event {ev.name}",
                    message=(
                        f"entity '{ev.entity}' is not in 02_concepts/candidate-concepts.yaml"
                    ),
                )
            )
    return warnings


def lint_unknown_transition_trigger(
    lifecycles: list[LifecycleEntry],
    all_event_names: set[str],
) -> list[LintWarning]:
    """Flag lifecycle transition triggers that don't resolve to a known event name."""
    warnings: list[LintWarning] = []
    event_fold = {n.casefold() for n in all_event_names}
    for lc in lifecycles:
        for t in lc.transitions:
            if t.trigger.casefold() not in event_fold:
                warnings.append(
                    LintWarning(
                        rule="unknown_transition_trigger",
                        concept=f"lifecycle {lc.entity}",
                        message=(
                            f"transition {t.from_state} → {t.to_state} uses trigger "
                            f"'{t.trigger}' which is not an event in this ingest or events.yaml"
                        ),
                    )
                )
    return warnings


def lint_unknown_speaker_in_quotes(
    lifecycles: list[LifecycleEntry],
    events: list[EventEntry],
    known_speakers: set[str],
) -> list[LintWarning]:
    """Flag source_quote speakers that don't resolve to a known stakeholder."""
    warnings: list[LintWarning] = []
    for lc in lifecycles:
        for sq in lc.source_quotes:
            if _normalise_name(sq.source) not in known_speakers:
                warnings.append(
                    LintWarning(
                        rule="unknown_speaker",
                        concept=f"lifecycle {lc.entity}",
                        message=f"quote attributed to \"{sq.source}\" has no matching stakeholder",
                    )
                )
    for ev in events:
        for sq in ev.source_quotes:
            if _normalise_name(sq.source) not in known_speakers:
                warnings.append(
                    LintWarning(
                        rule="unknown_speaker",
                        concept=f"event {ev.name}",
                        message=f"quote attributed to \"{sq.source}\" has no matching stakeholder",
                    )
                )
    return warnings


def run_lints(
    new_lifecycles: list[LifecycleEntry],
    new_events: list[EventEntry],
    existing_lifecycles: list[LifecycleEntry],
    existing_events: list[EventEntry],
    known_concepts: set[str],
    known_speakers: set[str],
) -> list[LintWarning]:
    all_event_names = {e.name for e in new_events} | {e.name for e in existing_events}
    warnings: list[LintWarning] = []
    warnings.extend(lint_unknown_entity(new_lifecycles, new_events, known_concepts))
    warnings.extend(lint_unknown_transition_trigger(new_lifecycles, all_event_names))
    warnings.extend(lint_event_not_past_tense(new_events))
    warnings.extend(lint_unknown_speaker_in_quotes(new_lifecycles, new_events, known_speakers))
    return warnings


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------

@dataclass
class MergeReport:
    lifecycles_added: list[str] = field(default_factory=list)
    lifecycles_updated: list[str] = field(default_factory=list)
    events_added: list[str] = field(default_factory=list)
    events_updated: list[str] = field(default_factory=list)


def merge_lifecycles(
    existing: list[LifecycleEntry], new: list[LifecycleEntry],
    session: str, interviewer: str, at: datetime,
) -> tuple[list[LifecycleEntry], list[str], list[str]]:
    by_key: dict[str, LifecycleEntry] = {lc.entity.casefold(): lc for lc in existing}
    order: list[str] = [lc.entity.casefold() for lc in existing]
    added: list[str] = []
    updated: list[str] = []

    provenance = make_provenance(session, interviewer, at)

    for n in new:
        key = n.entity.casefold()
        if key in by_key:
            prev = by_key[key]

            state_index: dict[str, StateDef] = {s.name: s for s in prev.states}
            for s in n.states:
                state_index[s.name] = s  # new wins
            merged_states = list(state_index.values())

            seen_transitions = {(t.from_state, t.to_state, t.trigger) for t in prev.transitions}
            merged_transitions = list(prev.transitions)
            for t in n.transitions:
                k = (t.from_state, t.to_state, t.trigger)
                if k not in seen_transitions:
                    merged_transitions.append(t)
                    seen_transitions.add(k)

            merged_inv = list(prev.invariants)
            seen_i = {v.casefold() for v in merged_inv}
            for v in n.invariants:
                if v.casefold() not in seen_i:
                    merged_inv.append(v)
                    seen_i.add(v.casefold())

            merged_quotes = list(prev.source_quotes)
            seen_q = {(q.quote, q.source) for q in merged_quotes}
            for q in n.source_quotes:
                if (q.quote, q.source) not in seen_q:
                    merged_quotes.append(q)
                    seen_q.add((q.quote, q.source))

            by_key[key] = LifecycleEntry(
                entity=prev.entity,
                states=merged_states,
                transitions=merged_transitions,
                invariants=merged_inv,
                source_quotes=merged_quotes,
                last_ingested=provenance,
            )
            updated.append(prev.entity)
        else:
            by_key[key] = LifecycleEntry(
                entity=n.entity,
                states=n.states,
                transitions=n.transitions,
                invariants=n.invariants,
                source_quotes=n.source_quotes,
                last_ingested=provenance,
            )
            order.append(key)
            added.append(n.entity)

    return [by_key[k] for k in order], added, updated


def merge_events(
    existing: list[EventEntry], new: list[EventEntry],
    session: str, interviewer: str, at: datetime,
) -> tuple[list[EventEntry], list[str], list[str]]:
    by_key: dict[str, EventEntry] = {e.name.casefold(): e for e in existing}
    order: list[str] = [e.name.casefold() for e in existing]
    added: list[str] = []
    updated: list[str] = []

    provenance = make_provenance(session, interviewer, at)

    for n in new:
        key = n.name.casefold()
        if key in by_key:
            prev = by_key[key]

            merged_carries = list(prev.carries)
            seen_c = {c.casefold() for c in merged_carries}
            for c in n.carries:
                if c.casefold() not in seen_c:
                    merged_carries.append(c)
                    seen_c.add(c.casefold())

            merged_consumed = list(prev.consumed_by)
            seen_cb = {c.casefold() for c in merged_consumed}
            for c in n.consumed_by:
                if c.casefold() not in seen_cb:
                    merged_consumed.append(c)
                    seen_cb.add(c.casefold())

            merged_quotes = list(prev.source_quotes)
            seen_q = {(q.quote, q.source) for q in merged_quotes}
            for q in n.source_quotes:
                if (q.quote, q.source) not in seen_q:
                    merged_quotes.append(q)
                    seen_q.add((q.quote, q.source))

            by_key[key] = EventEntry(
                name=prev.name,
                domain=n.domain,
                entity=n.entity,
                triggered_by=n.triggered_by,
                carries=merged_carries,
                consumed_by=merged_consumed,
                source_quotes=merged_quotes,
                last_ingested=provenance,
            )
            updated.append(prev.name)
        else:
            by_key[key] = EventEntry(
                name=n.name,
                domain=n.domain,
                entity=n.entity,
                triggered_by=n.triggered_by,
                carries=n.carries,
                consumed_by=n.consumed_by,
                source_quotes=n.source_quotes,
                last_ingested=provenance,
            )
            order.append(key)
            added.append(n.name)

    return [by_key[k] for k in order], added, updated


# ---------------------------------------------------------------------------
# YAML writers
# ---------------------------------------------------------------------------

def write_lifecycles_yaml(entries: list[LifecycleEntry], path: str) -> None:
    def to_dict(lc: LifecycleEntry) -> dict:
        d: dict = {"entity": lc.entity}
        d["states"] = [{"name": s.name, "description": s.description} for s in lc.states]
        d["transitions"] = [
            {"from": t.from_state, "to": t.to_state, "trigger": t.trigger}
            for t in lc.transitions
        ]
        if lc.invariants:
            d["invariants"] = list(lc.invariants)
        if lc.source_quotes:
            d["source_quotes"] = [
                {"quote": q.quote, "source": q.source, "date": q.date}
                for q in lc.source_quotes
            ]
        if lc.last_ingested is not None:
            d["last_ingested"] = dict(lc.last_ingested)
        return d

    write_yaml_list([to_dict(lc) for lc in entries], path)


def write_events_yaml(entries: list[EventEntry], path: str) -> None:
    def to_dict(e: EventEntry) -> dict:
        d: dict = {
            "name": e.name,
            "domain": e.domain,
            "entity": e.entity,
            "triggered_by": e.triggered_by,
            "carries": list(e.carries),
        }
        if e.consumed_by:
            d["consumed_by"] = list(e.consumed_by)
        if e.source_quotes:
            d["source_quotes"] = [
                {"quote": q.quote, "source": q.source, "date": q.date}
                for q in e.source_quotes
            ]
        if e.last_ingested is not None:
            d["last_ingested"] = dict(e.last_ingested)
        return d

    write_yaml_list([to_dict(e) for e in entries], path)


# ---------------------------------------------------------------------------
# Warnings labels
# ---------------------------------------------------------------------------

BEHAVIOR_WARNING_LABELS: dict[str, str] = {
    "unknown_entity": "Entities not in candidate-concepts.yaml",
    "unknown_transition_trigger": "Lifecycle transition triggers with no matching event",
    "event_not_past_tense": "Events with non-past-tense names",
    "unknown_speaker": "Source quotes with unknown speakers",
}

BEHAVIOR_WARNING_ORDER: list[str] = [
    "unknown_entity",
    "unknown_transition_trigger",
    "event_not_past_tense",
    "unknown_speaker",
]


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

@dataclass
class IngestResult:
    lifecycles_total: int
    events_total: int
    report: MergeReport
    warnings: list[LintWarning]
    lifecycles_path: str
    events_path: str
    warnings_path: str


def ingest_behavior(
    workspace_path: str,
    fixture_path: str,
    session: str,
    interviewer: str,
    at: datetime | None = None,
) -> IngestResult:
    if at is None:
        at = datetime.now(timezone.utc)

    if not os.path.isfile(fixture_path):
        raise FileNotFoundError(f"ingest source not found: {fixture_path}")

    import yaml
    with open(fixture_path) as f:
        raw = yaml.safe_load(f) or {}

    if not isinstance(raw, dict):
        raise SchemaError(["Top-level YAML must be a mapping with 'lifecycles' and/or 'events' keys"])

    if "lifecycles" not in raw and "events" not in raw:
        raise SchemaError(["Input must have at least one of 'lifecycles' or 'events' keys"])

    new_lifecycles = parse_lifecycles(raw.get("lifecycles", []) or [])
    new_events = parse_events(raw.get("events", []) or [])

    lifecycles_path = os.path.join(workspace_path, "04_behavior", "lifecycle-states.yaml")
    events_path = os.path.join(workspace_path, "04_behavior", "events.yaml")

    existing_lifecycles = load_lifecycles_yaml(lifecycles_path)
    existing_events = load_events_yaml(events_path)

    known_concepts = {c.name for c in load_concepts_yaml(
        os.path.join(workspace_path, "02_concepts", "candidate-concepts.yaml")
    )}
    known_speakers = load_stakeholder_names(
        os.path.join(workspace_path, "00_scope", "stakeholders.yaml")
    )

    warnings = run_lints(
        new_lifecycles, new_events, existing_lifecycles, existing_events,
        known_concepts, known_speakers,
    )

    merged_lifecycles, lc_added, lc_updated = merge_lifecycles(
        existing_lifecycles, new_lifecycles, session=session, interviewer=interviewer, at=at,
    )
    merged_events, ev_added, ev_updated = merge_events(
        existing_events, new_events, session=session, interviewer=interviewer, at=at,
    )

    if new_lifecycles:
        write_lifecycles_yaml(merged_lifecycles, lifecycles_path)
    if new_events:
        write_events_yaml(merged_events, events_path)

    warnings_path = os.path.join(workspace_path, "ingest-warnings.md")
    write_warnings_file(
        warnings, warnings_path, session=session, interviewer=interviewer, at=at,
        item_kind="entry",
        rule_labels=BEHAVIOR_WARNING_LABELS,
        rule_order=BEHAVIOR_WARNING_ORDER,
    )

    report = MergeReport(
        lifecycles_added=lc_added,
        lifecycles_updated=lc_updated,
        events_added=ev_added,
        events_updated=ev_updated,
    )

    return IngestResult(
        lifecycles_total=len(merged_lifecycles),
        events_total=len(merged_events),
        report=report,
        warnings=warnings,
        lifecycles_path=lifecycles_path,
        events_path=events_path,
        warnings_path=warnings_path,
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _print_summary(result: IngestResult, root: str) -> None:
    r = result.report
    print("Ingested behavior into:")
    print(f"  {os.path.relpath(result.lifecycles_path, root)}")
    print(f"  {os.path.relpath(result.events_path, root)}")
    print("")
    print(f"Lifecycles — added: {len(r.lifecycles_added)} ({', '.join(r.lifecycles_added) or '—'})")
    print(f"              updated: {len(r.lifecycles_updated)} ({', '.join(r.lifecycles_updated) or '—'})")
    print(f"              total: {result.lifecycles_total}")
    print(f"Events     — added: {len(r.events_added)} ({', '.join(r.events_added) or '—'})")
    print(f"              updated: {len(r.events_updated)} ({', '.join(r.events_updated) or '—'})")
    print(f"              total: {result.events_total}")
    print("")
    if not result.warnings:
        print("Lint: clean — no warnings.")
    else:
        print(f"Lint: {len(result.warnings)} warning(s) — see {os.path.relpath(result.warnings_path, root)}")


def main() -> None:
    run_ingest_cli(
        prog="gnosis ingest behavior",
        description="Ingest LLM-extracted lifecycles + events into 04_behavior/*.yaml.",
        source_help="Path to the combined LLM-output YAML file.",
        ingest_fn=ingest_behavior,
        print_summary=_print_summary,
    )


if __name__ == "__main__":
    main()
