from datetime import UTC, datetime

import pytest
from pydantic import ValidationError


def test_telemetry_requires_timezone_and_valid_ranges():
    from hydro_agent.models import Telemetry

    valid = dict(
        asset_id="TR-1042",
        timestamp=datetime.now(UTC),
        temperature_c=88.2,
        load_pct=92,
        baseline_stddev=3.7,
        oil_degradation_confirmed=True,
    )
    assert Telemetry(**valid).baseline_stddev == 3.7
    with pytest.raises(ValidationError):
        Telemetry(**(valid | {"timestamp": "2026-10-07T13:00:00"}))
    with pytest.raises(ValidationError):
        Telemetry(**(valid | {"load_pct": -1}))


def test_prediction_is_bounded_and_extra_fields_rejected():
    from hydro_agent.models import Prediction

    valid = dict(
        asset_id="TR-1042",
        failure_probability_30d=0.68,
        risk_level="high",
        main_factors=["température"],
        model_version="simulation-v1",
    )
    assert Prediction(**valid).failure_probability_30d == 0.68
    for update in ({"failure_probability_30d": 1.5}, {"approved_by": "modele"}):
        with pytest.raises(ValidationError):
            Prediction(**(valid | update))


def test_settings_read_uv_project_environment(monkeypatch):
    from hydro_agent.config import Settings

    monkeypatch.setenv("OPENROUTER_API_KEY", "secret-de-test")
    settings = Settings(_env_file=None)
    assert settings.openrouter_api_key.get_secret_value() == "secret-de-test"
    assert "secret-de-test" not in repr(settings)
    assert settings.role == "operator"
