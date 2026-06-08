"""Tests for the Freelancer collector — httpx mocked, no real network calls."""

from unittest.mock import MagicMock, patch

from src.collectors.freelancer import FreelancerCollector, _to_opportunity
from src.models import Opportunity

# A sample project shaped like the Freelancer API response.
_SAMPLE_PROJECT = {
    "id": 12345,
    "title": "Build a FastAPI backend",
    "type": "fixed",
    "budget": {"minimum": 250, "maximum": 750},
    "currency": {"code": "USD"},
    "preview_description": "Need a REST API in Python with FastAPI and PostgreSQL.",
    "upgrades": {"verified": True},
}


def test_to_opportunity_mapeia_campos():
    """A raw Freelancer project maps into a proper Opportunity."""
    opp = _to_opportunity(_SAMPLE_PROJECT)
    assert isinstance(opp, Opportunity)
    assert opp.id == "12345"
    assert opp.platform == "Freelancer"
    assert opp.title == "Build a FastAPI backend"
    assert opp.price_model == "fixed"
    assert opp.budget == 750.0  # uses maximum
    assert opp.currency == "USD"
    assert opp.payment_verified is True


def test_to_opportunity_campos_faltando_usa_defaults():
    """Missing nested fields fall back to safe defaults instead of crashing."""
    opp = _to_opportunity({"id": 1, "title": "x"})
    assert opp.budget == 0.0
    assert opp.currency == "USD"
    assert opp.payment_verified is False


def test_collect_sem_token_retorna_vazio(monkeypatch):
    """No token -> empty list, no crash, source simply skipped."""
    monkeypatch.delenv("FREELANCER_OAUTH_TOKEN", raising=False)
    collector = FreelancerCollector()
    assert collector.collect() == []


def test_collect_sucesso_mapeia_projetos(monkeypatch):
    """A successful API response is mapped into Opportunity objects."""
    monkeypatch.setenv("FREELANCER_OAUTH_TOKEN", "fake-token")
    fake_response = MagicMock(status_code=200)
    fake_response.raise_for_status = MagicMock()
    fake_response.json = MagicMock(
        return_value={"result": {"projects": [_SAMPLE_PROJECT, _SAMPLE_PROJECT]}}
    )

    with patch("src.collectors.freelancer.httpx.get", return_value=fake_response):
        collector = FreelancerCollector()
        results = collector.collect()

    assert len(results) == 2
    assert all(isinstance(o, Opportunity) for o in results)


def test_collect_falha_de_rede_retorna_vazio(monkeypatch):
    """A network error returns an empty list instead of raising."""
    monkeypatch.setenv("FREELANCER_OAUTH_TOKEN", "fake-token")
    with patch("src.collectors.freelancer.httpx.get", side_effect=Exception("network down")):
        collector = FreelancerCollector()
        assert collector.collect() == []
