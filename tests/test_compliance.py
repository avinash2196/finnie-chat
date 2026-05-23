from app.agents.compliance import run as compliance_run


def test_no_disclaimer_for_low_risk():
    output = compliance_run("What is a stock?", "LOW")
    assert "financial advice" not in output.lower()


def test_disclaimer_for_med_risk():
    output = compliance_run("Is ETF safer than stocks?", "MED")
    assert "financial advice" in output.lower()
