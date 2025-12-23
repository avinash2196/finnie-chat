import pytest
from app.agents.compliance import run


def test_disclaimer_appended_for_med_high():
    base = "This is a response"
    out = run(base, risk="MED")
    assert "educational information" in out


def test_disclaimer_not_duplicated_if_present():
    disclaimer = "(Note: This is educational information, not financial advice.)"
    text = f"Answer. {disclaimer}"
    out = run(text, risk="HIGH")
    # Should not duplicate disclaimer
    assert out.count(disclaimer) == 1


def test_no_disclaimer_for_low_risk():
    base = "Short answer"
    out = run(base, risk="LOW")
    assert "educational information" not in out
