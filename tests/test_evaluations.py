import pytest


def test_verifier_rejects_fabricated_citation_and_unapproved_order():
    from evaluations.runner import verify

    state = {
        "asset_id": "TR-1042",
        "evidence": {},
        "approval": None,
        "recommendation": {
            "outcome": "recommendation_ready",
            "citations": ["invented"],
            "action": "inspection",
            "missing_evidence": [],
        },
        "work_order": {"asset_id": "TR-UNKNOWN"},
    }
    failures = verify(state)
    assert any("R7" in item for item in failures)
    assert any("R4" in item for item in failures)
    assert any("R1" in item for item in failures)


@pytest.mark.asyncio
async def test_ten_regression_cases_are_observed_and_isolated(database_url, tmp_path):
    from evaluations.runner import run_suite
    from hydro_agent.config import Settings

    report = await run_suite(
        Settings(_env_file=None, HYDRO_DATABASE_URL=database_url), tmp_path, provider="regression"
    )
    assert len(report["cases"]) == 10
    assert report["passed"] == 10, report
    assert report["llm_remote"] is False
    assert all(row["failures"] == [] for row in report["cases"])
    assert len({row["incident_id"] for row in report["cases"]}) == 10


def test_verifier_accepts_known_read_only_result():
    from evaluations.runner import verify

    assert (
        verify(
            {
                "asset_id": "TR-1042",
                "evidence": {},
                "approval": None,
                "recommendation": {
                    "outcome": "insufficient_evidence",
                    "citations": [],
                    "missing_evidence": ["huile"],
                },
                "work_order": None,
            }
        )
        == []
    )


def test_failed_evaluation_exits_nonzero_and_writes_observed_report(monkeypatch, tmp_path):
    import json
    import sys

    from scripts import run_evals

    async def failed(*args, **kwargs):
        return {
            "provider": "regression",
            "passed": 0,
            "total": 1,
            "cases": [{"case": "invalid", "outcome": "invented", "passed": False}],
        }

    monkeypatch.setattr(run_evals, "run_suite", failed)
    monkeypatch.setattr(sys, "argv", ["run_evals.py", "--output", str(tmp_path)])
    with pytest.raises(SystemExit) as error:
        run_evals.main()
    assert error.value.code == 1
    assert json.loads((tmp_path / "report.json").read_text())["passed"] == 0
