import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import psycopg
import pytest
from conftest import DATA

from hydro_agent.models import DomainError
from hydro_agent.services.data import DataService


def test_concurrent_initialization_and_begin_create_one_incident(database_url):
    from hydro_agent.state.postgres import IncidentRepository

    event = DataService(DATA).get_event("EVT-48392")
    with ThreadPoolExecutor(max_workers=6) as pool:
        states = list(pool.map(lambda _: IncidentRepository(database_url).begin(event), range(12)))
    assert len({state["incident_id"] for state in states}) == 1
    assert all(state["event"] == event.model_dump(mode="json") for state in states)
    with psycopg.connect(database_url) as connection:
        assert connection.execute("SELECT count(*) FROM incidents").fetchone()[0] == 1
        assert (
            connection.execute("SELECT pg_typeof(payload)::text FROM incidents").fetchone()[0]
            == "jsonb"
        )


def test_transaction_rolls_back_partial_mutation(registry):
    with pytest.raises(RuntimeError):
        with registry.repository._transaction() as connection:
            connection.execute("UPDATE incidents SET payload='{}'::jsonb")
            raise RuntimeError("Interruption simulée.")
    assert registry.repository.get(registry.incident_id)["status"] == "new"


def test_session_lock_blocks_other_process_and_releases_on_exit(registry):
    code = """
import sys
from hydro_agent.models import DomainError
from hydro_agent.state.postgres import IncidentRepository
repository = IncidentRepository(sys.stdin.readline().strip())
try:
    with repository.investigation(sys.argv[1]):
        print('acquired', flush=True)
except DomainError:
    print('blocked', flush=True)
"""

    def child():
        return subprocess.run(
            [sys.executable, "-c", code, registry.incident_id],
            input=registry.repository.database_url + "\n",
            text=True,
            capture_output=True,
            timeout=20,
        )

    with registry.repository.investigation(registry.incident_id):
        result = child()
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "blocked"
    assert child().stdout.strip() == "acquired"


def test_database_failure_does_not_expose_credentials():
    from hydro_agent.state.postgres import IncidentRepository

    with pytest.raises(DomainError) as error:
        IncidentRepository("postgresql://private-user:private-password@127.0.0.1:1/absent")
    assert "PostgreSQL" in str(error.value)
    assert "private" not in str(error.value)
