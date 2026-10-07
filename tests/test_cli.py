import json
import os
import subprocess
import sys

from conftest import DATA, collect_evidence, draft


def run_cli(database_url, *args, role="operator"):
    env = {
        **os.environ,
        "HYDRO_DATA_DIR": str(DATA),
        "HYDRO_DATABASE_URL": database_url,
        "HYDRO_ROLE": role,
        "HYDRO_ACTOR": "personne-test",
        "OPENROUTER_API_KEY": "",
        "AZURE_AI_PROJECT_ENDPOINT": "",
        "AZURE_AI_AGENT_VERSION": "",
    }
    return subprocess.run(
        [sys.executable, "-m", "hydro_agent.cli", *args],
        env=env,
        text=True,
        capture_output=True,
        timeout=20,
    )


def test_cli_help_is_french_and_missing_key_is_actionable(database_url):
    help_result = run_cli(database_url, "--help")
    assert help_result.returncode == 0
    assert "Investigation" in help_result.stdout
    result = run_cli(database_url, "investigate", "EVT-48392")
    assert result.returncode == 1
    assert "OPENROUTER_API_KEY" in result.stderr
    assert "Traceback" not in result.stderr


def test_foundry_without_configuration_never_falls_back_to_openrouter(database_url):
    result = run_cli(database_url, "investigate", "EVT-48392", "--provider", "foundry")
    assert result.returncode == 1
    assert "AZURE_AI_PROJECT_ENDPOINT" in result.stderr
    assert "OPENROUTER_API_KEY" not in result.stderr
    assert "Traceback" not in result.stderr


def test_publish_foundry_requires_configuration_without_openrouter(database_url):
    result = run_cli(database_url, "publish-foundry")
    assert result.returncode == 1
    assert "AZURE_AI_PROJECT_ENDPOINT" in result.stderr
    assert "OPENROUTER_API_KEY" not in result.stderr


async def test_cli_approval_resume_and_restart_are_separate(registry, database_url):
    # Même base que la CLI, redémarrée à chaque commande.
    await collect_evidence(registry)
    assert (await draft(registry)).ok
    denied = run_cli(database_url, "approve", registry.incident_id)
    assert denied.returncode == 1
    approved = run_cli(database_url, "approve", registry.incident_id, role="maintenance_supervisor")
    assert approved.returncode == 0, approved.stderr
    assert json.loads(approved.stdout)["status"] == "approved"
    first = run_cli(database_url, "resume", registry.incident_id)
    second = run_cli(database_url, "resume", registry.incident_id)
    assert first.returncode == second.returncode == 0
    assert json.loads(first.stdout) == json.loads(second.stdout)
    assert json.loads(first.stdout)["simulated"] is True
