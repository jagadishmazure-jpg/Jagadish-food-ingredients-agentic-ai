"""Guard tests for the Scope and assumptions block in docs/architecture.md.

The block states who the system is for, what the agents may do on their
own, and what the design assumes. These tests pin its presence, its
required labels, and its position ahead of the architecture diagram so
the scoping statements cannot silently drop out of the design document.
"""

from pathlib import Path

_ARCHITECTURE = Path(__file__).resolve().parents[1] / "docs" / "architecture.md"

_HEADING = "## Scope and assumptions"


def _text():
    return _ARCHITECTURE.read_text(encoding="utf-8")


def _scope_section():
    text = _text()
    start = text.index(_HEADING)
    end = text.find("\n## ", start + len(_HEADING))
    return text[start:end if end != -1 else len(text)]


# --- the block exists and sits ahead of the diagram -------------------------

def test_scope_section_exists():
    assert _HEADING in _text()


def test_scope_section_before_diagram():
    text = _text()
    diagram_at = min(
        i
        for i in (
            text.find("flowchart"),
            text.find("```mermaid"),
            text.find("## Multi-agent architecture"),
        )
        if i != -1
    )
    assert text.index(_HEADING) < diagram_at


# --- required labels ----------------------------------------------------------

def test_scoping_answer_labels_present():
    section = _scope_section()
    for label in (
        "User and problem",
        "Outcome",
        "AI's part of the workflow",
        "Agency per action",
    ):
        assert label in section, f"missing scoping answer: {label}"


def test_assumption_bucket_labels_present():
    section = _scope_section()
    assumptions = section[section.index("### Assumptions"):]
    for label in (
        "Data",
        "Inputs",
        "Operating constraints",
        "Action risk",
    ):
        assert label in assumptions, f"missing assumption bucket: {label}"
