"""Test Tax Education Agent"""
import pytest
from app.agents.tax_education import run


class TestTaxEducationAgent:
    """Tests for Tax Education Agent"""

    def test_tax_education_ira_explanation(self):
        """Test tax education agent with IRA question"""
        message = "What is a Roth IRA?"
        result = run(message)
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "IRA" in result or "after-tax" in result or "tax-free" in result.lower()

    def test_tax_education_capital_gains(self):
        """Test tax education agent with capital gains question"""
        message = "How are capital gains taxed?"
        result = run(message)
        
        assert isinstance(result, str)
        assert "capital" in result.lower() or "gains" in result.lower() or "tax" in result.lower()

    def test_tax_education_traditional_ira(self):
        """Test tax education agent with Traditional IRA question"""
        message = "Tell me about Traditional IRAs"
        result = run(message)
        
        assert isinstance(result, str)
        assert len(result) > 0

    def test_tax_education_401k_question(self):
        """Test tax education agent with 401k question"""
        message = "What are 401k accounts?"
        result = run(message)
        
        assert isinstance(result, str)
        assert len(result) > 0

    def test_tax_education_generic_tax_question(self):
        """Test tax education agent with generic tax question"""
        message = "How should I manage my taxes?"
        result = run(message)
        
        assert isinstance(result, str)
        assert "tax" in result.lower() or "professional" in result.lower()

    def test_tax_education_empty_message(self):
        """Test tax education agent with empty message"""
        message = ""
        result = run(message)
        
        assert isinstance(result, str)
        assert len(result) > 0

    def test_tax_education_account_type_question(self):
        """Test tax education agent with account type question"""
        message = "What types of tax-advantaged accounts exist?"
        result = run(message)
        
        assert isinstance(result, str)
        assert len(result) > 0

    def test_tax_education_long_term_gains(self):
        """Test tax education agent recognizes long-term capital gains"""
        message = "Are long-term capital gains taxed differently?"
        result = run(message)
        
        assert isinstance(result, str)
        assert "long-term" in result.lower() or "preferential" in result.lower() or "rates" in result.lower()

    def test_tax_education_with_user_id(self):
        """Test tax education agent with user_id parameter"""
        message = "Explain Roth conversions"
        result = run(message, user_id="user_123")
        
        assert isinstance(result, str)
        assert len(result) > 0

    def test_tax_education_return_type(self):
        """Test that tax education agent always returns string"""
        messages = [
            "What is tax-loss harvesting?",
            "IRA contribution limits?",
            "Tell me about taxable accounts",
        ]
        
        for msg in messages:
            result = run(msg)
            assert isinstance(result, str)
