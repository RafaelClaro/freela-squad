"""Tests for Camada 1 filters — deterministic, no Claude calls."""

from src import filters


def test_stack_incompativel_descartado(opportunities):
    """#2 (React Native) must be cut by the stack filter."""
    result = filters.apply_filters(opportunities["2"])
    assert result.passed is False
    assert "Stack" in result.reason


def test_prazo_curto_descartado(opportunities):
    """#4 (12 hours) must be cut by the deadline filter."""
    result = filters.apply_filters(opportunities["4"])
    assert result.passed is False
    assert "Prazo" in result.reason


def test_brl_passa_para_camada_2(opportunities):
    """#3 and #6 (BRL) must pass Camada 1 — currency is decided in Camada 2."""
    assert filters.apply_filters(opportunities["3"]).passed is True
    assert filters.apply_filters(opportunities["6"]).passed is True


def test_caso_modelo_passa(opportunities):
    """#1 (clean USD API project) must pass Camada 1."""
    assert filters.apply_filters(opportunities["1"]).passed is True
