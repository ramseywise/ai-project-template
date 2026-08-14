"""Unit tests for the run report renderer (evals/generation/report.py).

These are the module's importer of record. Before them, report.py was reached
by nothing: `python -m evals.pipelines.run` builds its own summary, so the
formatter shipped in every scaffold with no caller and no test, and only
`scripts/check_imports.py` noticed.

The report is what a human actually reads after an eval run, so the properties
worth pinning are the ones that make it readable and honest: every case appears
as a row, the headline numbers are carried through verbatim, and a failure is
visible as a failure rather than rendering as an ordinary row.

Pure Python over hand-built ``CaseResult`` rows — no LLM calls, no I/O.
"""

from __future__ import annotations

from typing import Any

from evals.generation.report import format_report, summarize_table
from evals.generation.results import CaseResult


def _result(**overrides: object) -> CaseResult:
    base: dict[str, object] = {
        "case_id": "c-1",
        "difficulty": "medium",
        "first_pass_valid": True,
        "repair_attempts": 0,
        "used_fallback": False,
        "grounded": True,
        "contract_valid": True,
        "llm_calls": 1,
        "error": None,
    }
    base.update(overrides)
    return CaseResult(**base)  # type: ignore[arg-type]


def _metrics(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "cases": 1,
        "contract_pass_rate": 100.0,
        "repair_convergence": 0.0,
        "fallback_rate": 0.0,
        "grounding_rate": 100.0,
        "contract_valid_rate": 100.0,
        "total_llm_calls": 1,
    }
    base.update(overrides)
    return base


class TestSummarizeTable:
    def test_renders_a_row_per_input_dict(self) -> None:
        table = summarize_table([{"a": "1", "b": "2"}, {"a": "3", "b": "4"}])

        # Header, separator, and one line per row.
        assert len(table.splitlines()) == 4
        assert "| a" in table
        assert "| 3" in table

    def test_columns_are_padded_to_the_widest_cell(self) -> None:
        # Ragged columns are the whole reason this helper exists rather than a
        # bare join — an unpadded table is unreadable in a terminal.
        table = summarize_table([{"name": "x"}, {"name": "a-much-longer-value"}])
        widths = {len(line) for line in table.splitlines()}

        assert len(widths) == 1, f"rows have inconsistent widths: {widths}"

    def test_empty_input_says_so_rather_than_rendering_an_empty_table(self) -> None:
        assert summarize_table([]) == "_no rows_"


class TestFormatReport:
    def test_every_case_appears_in_the_table(self) -> None:
        results = [_result(case_id="c-1"), _result(case_id="c-2"), _result(case_id="c-3")]

        report = format_report(results, _metrics(cases=3))

        for case_id in ("c-1", "c-2", "c-3"):
            assert case_id in report

    def test_headline_metrics_are_carried_through_verbatim(self) -> None:
        # FAILS IF: the formatter recomputes any of these instead of printing
        # what metrics.py produced. Two sources of truth for a pass rate is how
        # a report and its gate come to disagree.
        report = format_report(
            [_result()],
            _metrics(contract_pass_rate=62.5, fallback_rate=12.5, grounding_rate=87.5),
        )

        assert "62.5" in report
        assert "12.5" in report
        assert "87.5" in report

    def test_an_invalid_case_is_visually_distinct(self) -> None:
        # The valid column renders "NO" upper-case precisely so a failed case is
        # scannable in a wall of yes/no. Losing that is a readability
        # regression a pass-rate assertion would not catch.
        report = format_report([_result(contract_valid=False)], _metrics(contract_valid_rate=0.0))

        assert "NO" in report

    def test_errors_are_listed_with_their_case_id(self) -> None:
        report = format_report(
            [_result(case_id="c-boom", error="provider timeout")],
            _metrics(),
        )

        assert "Errors:" in report
        assert "c-boom" in report
        assert "provider timeout" in report

    def test_no_error_section_when_every_case_succeeded(self) -> None:
        assert "Errors:" not in format_report([_result()], _metrics())

    def test_unconverged_repairs_render_as_na_not_none(self) -> None:
        # repair_convergence is None when no case converged. Printing a bare
        # "None" into a human report reads as a bug in the harness.
        report = format_report([_result()], _metrics(repair_convergence=None))

        assert "n/a" in report
        assert "None" not in report
