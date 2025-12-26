"""Test Goal Planning Agent"""
import pytest
from app.agents.goal_planning import run


class TestGoalPlanningAgent:
    """Tests for Goal Planning Agent"""

    def test_goal_planning_with_retirement_target(self):
        """Test goal planning agent with retirement target"""
        message = "I want to save $1M for retirement in 20 years"
        result = run(message)
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Goal" in result or "target" in result.lower()
        assert "$" in result or "savings" in result.lower()

    def test_goal_planning_with_savings_goal(self):
        """Test goal planning agent with savings goal"""
        message = "I need $50,000 in 5 years for a house down payment"
        result = run(message)
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "50" in result or "goal" in result.lower()

    def test_goal_planning_with_generic_message(self):
        """Test goal planning agent with generic message"""
        message = "Help me plan my finances"
        result = run(message)
        
        assert isinstance(result, str)
        assert len(result) > 0

    def test_goal_planning_empty_message(self):
        """Test goal planning agent with empty message"""
        message = ""
        result = run(message)
        
        assert isinstance(result, str)
        assert len(result) > 0

    def test_goal_planning_extracts_target_amount(self):
        """Test that goal planning extracts numeric targets"""
        message = "I want $500,000 in 15 years"
        result = run(message)
        
        assert isinstance(result, str)
        assert "$" in result or "500" in result

    def test_goal_planning_extracts_timeframe(self):
        """Test that goal planning extracts timeframe"""
        message = "I want to retire in 30 years with plenty of savings"
        result = run(message)
        
        assert isinstance(result, str)
        assert "30" in result or "years" in result.lower()

    def test_goal_planning_returns_suggested_steps(self):
        """Test that goal planning returns suggested steps"""
        message = "Planning for retirement"
        result = run(message)
        
        assert isinstance(result, str)
        assert "steps" in result.lower() or "Define" in result or "Calculate" in result

    def test_goal_planning_with_user_id(self):
        """Test goal planning agent with user_id parameter"""
        message = "I want to save $250K in 10 years"
        result = run(message, user_id="user_123")
        
        assert isinstance(result, str)
        assert len(result) > 0
