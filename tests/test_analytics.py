import json

import httpx
import pytest
from conftest import DATA

from hydro_agent.models import DomainError


def test_json_adapter_matches_existing_fixture_and_never_fills_missing_prediction(tmp_path):
    from hydro_agent.services.analytics import JsonAnalyticsService

    assert JsonAnalyticsService(DATA).predict("TR-1042").failure_probability_30d == 0.68
    (tmp_path / "predictions.json").write_text("[]")
    with pytest.raises(DomainError, match="indisponible"):
        JsonAnalyticsService(tmp_path).predict("TR-1042")


def test_databricks_adapter_sends_narrow_payload_and_validates_prediction():
    from hydro_agent.services.analytics import DatabricksAnalyticsService

    row = json.loads((DATA / "predictions.json").read_text())[0]

    def handler(request):
        assert request.headers["authorization"] == "Bearer SECRET"
        assert json.loads(request.content) == {"dataframe_records": [{"asset_id": "TR-1042"}]}
        return httpx.Response(200, json={"predictions": [row]})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        service = DatabricksAnalyticsService(
            "https://demo.cloud.databricks.com/serving-endpoints/risk/invocations",
            "SECRET",
            client=client,
        )
        assert service.predict("TR-1042").failure_probability_30d == 0.68


@pytest.mark.parametrize(
    "result",
    [
        {"predictions": []},
        {"predictions": [{"asset_id": "UNKNOWN"}]},
        {"predictions": [{"asset_id": "TR-1042", "failure_probability_30d": 1.5}]},
        {"unexpected": "SECRET"},
    ],
)
def test_invalid_remote_schema_has_no_fallback(result):
    from hydro_agent.services.analytics import DatabricksAnalyticsService

    with httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=result))
    ) as client:
        service = DatabricksAnalyticsService(
            "https://demo.azuredatabricks.net/serving-endpoints/risk/invocations",
            "SECRET",
            client=client,
        )
        with pytest.raises(DomainError) as error:
            service.predict("TR-1042")
        assert "SECRET" not in str(error.value)


@pytest.mark.parametrize("status", [401, 429, 500])
def test_http_failures_hide_credentials_and_response_body(status):
    from hydro_agent.services.analytics import DatabricksAnalyticsService

    with httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(status, text="SECRET"))
    ) as client:
        service = DatabricksAnalyticsService(
            "https://demo.cloud.databricks.com/serving-endpoints/risk/invocations",
            "SECRET",
            client=client,
        )
        with pytest.raises(DomainError) as error:
            service.predict("TR-1042")
        assert str(status) in str(error.value)
        assert "SECRET" not in str(error.value)


def test_timeout_never_returns_local_probability():
    from hydro_agent.services.analytics import DatabricksAnalyticsService

    def handler(request):
        raise httpx.ReadTimeout("SECRET", request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        service = DatabricksAnalyticsService(
            "https://demo.cloud.databricks.com/serving-endpoints/risk/invocations",
            "SECRET",
            client=client,
        )
        with pytest.raises(DomainError, match="indisponible") as error:
            service.predict("TR-1042")
        assert "SECRET" not in str(error.value)


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://attacker.example/serving-endpoints/risk/invocations",
        "https://demo.cloud.databricks.com.attacker.example/serving-endpoints/risk/invocations",
        "http://demo.cloud.databricks.com/serving-endpoints/risk/invocations",
        "https://SECRET@demo.cloud.databricks.com/serving-endpoints/risk/invocations",
        "https://demo.cloud.databricks.com/serving-endpoints/risk/invocations?token=SECRET",
    ],
)
def test_endpoint_rejected_before_credentials_are_used(endpoint):
    from hydro_agent.services.analytics import DatabricksAnalyticsService

    with pytest.raises(DomainError):
        DatabricksAnalyticsService(endpoint, "SECRET")


def test_unknown_asset_is_rejected_before_remote_call():
    from hydro_agent.services.data import DataService

    class NeverCalled:
        def predict(self, asset_id):
            pytest.fail("Un actif inconnu ne doit pas atteindre l’API.")

    data = DataService(DATA, analytics=NeverCalled())
    with pytest.raises(DomainError, match="Actif inconnu"):
        data.predict("UNKNOWN")


def test_valid_prediction_for_another_asset_is_rejected():
    from hydro_agent.services.analytics import DatabricksAnalyticsService

    other = json.loads((DATA / "predictions.json").read_text())[1]
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={"predictions": [other]})
        )
    ) as client:
        service = DatabricksAnalyticsService(
            "https://demo.cloud.databricks.com/serving-endpoints/risk/invocations",
            "SECRET",
            client=client,
        )
        with pytest.raises(DomainError, match="invalide"):
            service.predict("TR-1042")


def test_databricks_selection_without_configuration_is_not_silently_json(registry):
    from hydro_agent.config import Settings
    from hydro_agent.mcp.server import build_registry

    settings = Settings(
        _env_file=None,
        HYDRO_DATA_DIR=DATA,
        HYDRO_DATABASE_URL=registry.repository.database_url,
        HYDRO_ANALYTICS_BACKEND="databricks",
    )
    with pytest.raises(DomainError, match="Endpoint Databricks"):
        build_registry(settings, registry.incident_id)


@pytest.mark.parametrize("probability", [True, "0.68"])
def test_remote_probability_is_not_coerced(probability):
    from hydro_agent.services.analytics import DatabricksAnalyticsService

    row = json.loads((DATA / "predictions.json").read_text())[0]
    row["failure_probability_30d"] = probability
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={"predictions": [row]})
        )
    ) as client:
        service = DatabricksAnalyticsService(
            "https://demo.cloud.databricks.com/serving-endpoints/risk/invocations",
            "SECRET",
            client=client,
        )
        with pytest.raises(DomainError, match="invalide"):
            service.predict("TR-1042")
