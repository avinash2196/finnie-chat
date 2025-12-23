"""Tests for LLM utility functions."""

import pytest
from unittest.mock import patch, MagicMock
from app.llm import call_llm, get_gateway_metrics


class TestCallLLM:
    """Test LLM calling function."""
    
    @patch('app.llm.get_gateway')
    def test_call_llm_basic(self, mock_get_gateway):
        """Test basic LLM call."""
        mock_gateway = MagicMock()
        mock_gateway.call_llm.return_value = "This is a test response"
        mock_get_gateway.return_value = mock_gateway
        
        result = call_llm("System prompt", "What is a stock?")
        
        assert result == "This is a test response"
        mock_gateway.call_llm.assert_called_once()
    
    @patch('app.llm.get_gateway')
    def test_call_llm_with_temperature(self, mock_get_gateway):
        """Test LLM call with temperature parameter."""
        mock_gateway = MagicMock()
        mock_gateway.call_llm.return_value = "Response"
        mock_get_gateway.return_value = mock_gateway
        
        result = call_llm("System", "User prompt", temperature=0.8)
        
        assert result == "Response"
        # Verify temperature was passed as third positional arg
        mock_gateway.call_llm.assert_called_once_with("System", "User prompt", 0.8)
    
    @patch('app.llm.get_gateway')
    def test_call_llm_error_handling(self, mock_get_gateway):
        """Test LLM call handles errors gracefully."""
        mock_gateway = MagicMock()
        mock_gateway.call_llm.side_effect = Exception("API timeout")
        mock_get_gateway.return_value = mock_gateway
        
        with pytest.raises(Exception):
            call_llm("System", "Test")
    
    @patch('app.llm.get_gateway')
    def test_call_llm_empty_prompt(self, mock_get_gateway):
        """Test LLM call with empty prompt."""
        mock_gateway = MagicMock()
        mock_gateway.call_llm.return_value = "Empty prompt response"
        mock_get_gateway.return_value = mock_gateway
        
        result = call_llm("System", "")
        
        assert isinstance(result, str)
    
    @patch('app.llm.get_gateway')
    def test_call_llm_long_prompt(self, mock_get_gateway):
        """Test LLM call with very long prompt."""
        mock_gateway = MagicMock()
        mock_gateway.call_llm.return_value = "Long prompt response"
        mock_get_gateway.return_value = mock_gateway
        
        long_prompt = "test " * 1000  # Very long prompt
        result = call_llm("System", long_prompt)
        
        assert isinstance(result, str)


class TestGatewayMetrics:
    """Test gateway metrics function."""
    
    @patch('app.llm.get_gateway')
    def test_get_gateway_metrics(self, mock_get_gateway):
        """Test getting gateway metrics."""
        mock_gateway = MagicMock()
        mock_gateway.get_metrics.return_value = {
            'total_calls': 100,
            'cache_hits': 50,
            'failures': 5
        }
        mock_get_gateway.return_value = mock_gateway
        
        metrics = get_gateway_metrics()
        
        assert 'total_calls' in metrics
        assert metrics['total_calls'] == 100
    
    @patch('app.llm.get_gateway')
    def test_get_gateway_metrics_empty(self, mock_get_gateway):
        """Test metrics when none exist."""
        mock_gateway = MagicMock()
        mock_gateway.get_metrics.return_value = {}
        mock_get_gateway.return_value = mock_gateway
        
        metrics = get_gateway_metrics()
        
        assert isinstance(metrics, dict)
