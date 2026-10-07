import json
import os
import subprocess
import sys

from conftest import DATA, collect_evidence, draft

from hydro_agent.state.sqlite import IncidentRepository


def run_cli(tmp_path, *args, role="operator"):
    env = {
        **os.environ,
        "HYDRO_DATA_DIR": str(DATA),
        "HYDRO_DB_PATH": str(tmp_path / "cli.sqlite3"),
        "HYDRO_ROLE": role,
        "HYDRO_ACTOR": "personne-test",
        "OPENROUTER_API_KEY": "",
    }
    return subprocess.run(
        [sys.executable, "-m", "hydro_agent.cli", *args],
        env=env,
        text=True,
        capture_output=True,
        timeout=20,
    )


def test_cli_help_is_french_and_missing_key_is_actionable(tmp_path):
    help_result = run_cli(tmp_path, "--help")
    assert help_result.returncode == 0
    assert "Investigation" in help_result.stdout
    result = run_cli(tmp_path, "investigate", "EVT-48392")
    assert result.returncode == 1
    assert "OPENROUTER_API_KEY" in result.stderr
    assert "Traceback" not in result.stderr


async def test_cli_approval_resume_and_restart_are_separate(registry, tmp_path):
    # Même base que la CLI, redémarrée à chaque commande.
    registry.repository = IncidentRepository(tmp_path / "cli.sqlite3")
    state = registry.repository.begin(registry.event)
    registry.incident_id = state["incident_id"]
    await collect_evidence(registry)
    assert (await draft(registry)).ok
    denied = run_cli(tmp_path, "approve", registry.incident_id)
    assert denied.returncode == 1
    approved = run_cli(tmp_path, "approve", registry.incident_id, role="maintenance_supervisor")
    assert approved.returncode == 0, approved.stderr
    assert json.loads(approved.stdout)["status"] == "approved"
    first = run_cli(tmp_path, "resume", registry.incident_id)
    second = run_cli(tmp_path, "resume", registry.incident_id)
    assert first.returncode == second.returncode == 0
    assert json.loads(first.stdout) == json.loads(second.stdout)
    assert json.loads(first.stdout)["simulated"] is True
