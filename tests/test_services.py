import json
import shutil

import pytest
from conftest import DATA

from hydro_agent.models import DomainError


def test_telemetry_uses_event_time_not_wall_clock():
    from hydro_agent.services.data import DataService

    data = DataService(DATA)
    event = data.get_event("EVT-48392")
    rows = data.get_telemetry("TR-1042", event.timestamp, hours=24)
    assert len(rows) == 2
    assert rows[-1].baseline_stddev == 3.7
    assert all(row.timestamp <= event.timestamp for row in rows)
    assert len(data.get_telemetry("TR-1042", event.timestamp, hours=1)) == 1
    assert data.get_maintenance("TR-1042", event.timestamp)[0].work_order_id == "WO-11231"


def test_unknown_asset_and_unavailable_prediction(tmp_path):
    from hydro_agent.services.data import DataService

    shutil.copytree(DATA, tmp_path / "data")
    (tmp_path / "data/predictions.json").write_text("[]")
    data = DataService(tmp_path / "data")
    with pytest.raises(DomainError, match="inconnu"):
        data.get_asset("absent")
    with pytest.raises(DomainError, match="indisponible"):
        data.predict("TR-1042")


def test_search_accents_source_and_path_traversal():
    from hydro_agent.services.search import SearchService

    search = SearchService(DATA / "procedures")
    hits = search.search("surchauffe dégradation huile", limit=3)
    assert hits == search.search("surchauffe degradation huile", limit=3)
    assert any(hit["procedure_id"] == "TR-MAINT-004" for hit in hits)
    assert search.search("azertyinexistant") == []
    assert "24 heures" in search.get("TR-MAINT-004")["content"]
    with pytest.raises(DomainError):
        search.get("../assets")


def test_all_synthetic_rows_validate():
    from hydro_agent.models import Anomaly, Asset, Maintenance, Prediction, Telemetry

    for filename, model in [
        ("assets", Asset),
        ("anomalies", Anomaly),
        ("maintenance_history", Maintenance),
        ("predictions", Prediction),
        ("telemetry", Telemetry),
    ]:
        rows = json.loads((DATA / f"{filename}.json").read_text())
        assert rows
        for row in rows:
            model.model_validate(row)
