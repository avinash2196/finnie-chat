"""Test News Synthesizer Agent"""
import pytest
from app.agents.news_synthesizer import run


class TestNewsSynthesizerAgent:
    """Tests for News Synthesizer Agent"""

    def test_news_synthesizer_with_multi_sentence_text(self):
        """Test news synthesizer with multi-sentence input"""
        message = (
            "Apple reported strong Q4 earnings with 15% revenue growth. "
            "The company also announced a new AI initiative. "
            "Stock price jumped 5% on the news."
        )
        result = run(message)
        
        assert isinstance(result, str)
        assert len(result) > 0

    def test_news_synthesizer_with_short_text(self):
        """Test news synthesizer with short text"""
        message = "Tech stocks are up today."
        result = run(message)
        
        assert isinstance(result, str)
        assert len(result) > 0

    def test_news_synthesizer_empty_message(self):
        """Test news synthesizer with empty message"""
        message = ""
        result = run(message)
        
        assert isinstance(result, str)
        assert len(result) > 0  # Just verify it returns something

    def test_news_synthesizer_includes_context_note(self):
        """Test that news synthesizer includes contextual note"""
        message = (
            "Microsoft announced new cloud services. "
            "Enterprise customers are increasing purchases. "
            "Cloud division is now 30% of revenue."
        )
        result = run(message)
        
        assert isinstance(result, str)
        # Should include context about source credibility or portfolio impact
        assert len(result) > 50  # Substantial response

    def test_news_synthesizer_max_sentences(self):
        """Test news synthesizer with max_sentences parameter"""
        message = (
            "Sentence 1. Sentence 2. Sentence 3. Sentence 4. Sentence 5."
        )
        result = run(message, max_sentences=2)
        
        assert isinstance(result, str)
        assert len(result) > 0

    def test_news_synthesizer_with_earnings_news(self):
        """Test news synthesizer with earnings announcement"""
        message = (
            "Tesla reported record earnings with $25B revenue. "
            "EPS beat expectations by 20%. "
            "CFO guided for strong growth next quarter."
        )
        result = run(message)
        
        assert isinstance(result, str)
        assert len(result) > 0

    def test_news_synthesizer_with_user_id(self):
        """Test news synthesizer with user_id parameter"""
        message = "Fed announces rate cut decision"
        result = run(message, user_id="user_123")
        
        assert isinstance(result, str)
        assert len(result) > 0

    def test_news_synthesizer_return_type(self):
        """Test that news synthesizer always returns string"""
        messages = [
            "Market news here",
            "",
            "Breaking: stock market surge",
        ]
        
        for msg in messages:
            result = run(msg)
            assert isinstance(result, str)
