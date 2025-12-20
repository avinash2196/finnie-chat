"""Risk profiler for portfolio analysis."""

from app.mcp.market import get_client
from app.mcp.portfolio import get_portfolio_client
from app.llm import call_llm
import numpy as np
import logging

logger = logging.getLogger(__name__)


def calculate_portfolio_metrics(holdings_dict):
    """Calculate volatility, Sharpe ratio, beta.
    
    Args:
        holdings_dict: {
            'AAPL': {'quantity': 10, 'purchase_price': 150},
            'MSFT': {'quantity': 5, 'purchase_price': 300}
        }
    
    Returns:
        dict with 'volatility', 'avg_return', 'sharpe_ratio'
    """
    try:
        client = get_client()
        
        # Fetch current prices
        prices = {}
        for ticker in holdings_dict.keys():
            quote = client.get_quote(ticker)
            if quote.price is not None:
                prices[ticker] = quote.price
            else:
                logger.warning(f"Could not fetch price for {ticker}")
                return {
                    'volatility': None,
                    'avg_return': None,
                    'sharpe_ratio': None,
                    'error': f"Could not fetch price for {ticker}"
                }
        
        # Calculate returns (simplified - normally fetch historical)
        returns = []
        for ticker, price in prices.items():
            purchase_price = holdings_dict[ticker]['purchase_price']
            if purchase_price > 0:
                ret = (price - purchase_price) / purchase_price
                returns.append(ret)
        
        if not returns:
            return {
                'volatility': 0,
                'avg_return': 0,
                'sharpe_ratio': 0,
                'error': 'No valid returns calculated'
            }
        
        # Calculate portfolio metrics
        volatility = np.std(returns) * 100 if len(returns) > 1 else 0
        avg_return = np.mean(returns) * 100
        sharpe_ratio = avg_return / volatility if volatility > 0 else 0
        
        return {
            'volatility': round(volatility, 2),
            'avg_return': round(avg_return, 2),
            'sharpe_ratio': round(sharpe_ratio, 2)
        }
    
    except Exception as e:
        logger.error(f"Error calculating portfolio metrics: {e}")
        return {
            'volatility': None,
            'avg_return': None,
            'sharpe_ratio': None,
            'error': str(e)
        }


def run(user_message: str, holdings_dict: dict = None, user_id: str = "user_123"):
    """Main risk profiler agent.
    
    Args:
        user_message: User's query
        holdings_dict: Portfolio holdings to analyze (deprecated, use user_id instead)
        user_id: User identifier to fetch portfolio from MCP
    
    Returns:
        Risk analysis explanation from LLM
    """
    # If holdings_dict not provided, fetch from Portfolio MCP
    if holdings_dict is None:
        try:
            portfolio_client = get_portfolio_client(user_id)
            portfolio_result = portfolio_client.get_holdings()
            holdings_dict = portfolio_result.get('holdings', {})
        except Exception as e:
            logger.error(f"Error fetching portfolio from MCP: {e}")
            return f"Unable to fetch portfolio data: {e}"
    
    if not holdings_dict:
        return "No holdings to analyze. Please provide portfolio data."
    
    metrics = calculate_portfolio_metrics(holdings_dict)
    
    # Check for errors
    if metrics.get('error'):
        return f"Error analyzing portfolio: {metrics['error']}"
    
    # Use LLM to explain metrics
    try:
        explanation = call_llm(
            system_prompt="You are a risk assessment expert. Explain portfolio metrics clearly and simply.",
            user_prompt=f"""
Analyze these portfolio metrics and explain what they mean:

Portfolio Metrics:
- Volatility: {metrics['volatility']}%
- Expected Return: {metrics['avg_return']}%
- Sharpe Ratio: {metrics['sharpe_ratio']}

Holdings analyzed: {list(holdings_dict.keys())}

Question: {user_message}

Provide a clear, beginner-friendly explanation of what these metrics tell us about portfolio risk.
            """,
            temperature=0.3
        )
        return explanation
    
    except Exception as e:
        logger.error(f"Error in risk profiler LLM: {e}")
        return f"Risk Profile - Volatility: {metrics['volatility']}%, Return: {metrics['avg_return']}%, Sharpe Ratio: {metrics['sharpe_ratio']}"

    
    metrics = calculate_portfolio_metrics(holdings_dict)
    
    # Check for errors
    if metrics.get('error'):
        return f"Error analyzing portfolio: {metrics['error']}"
    
    # Use LLM to explain metrics
    try:
        explanation = call_llm(
            system_prompt="You are a risk assessment expert. Explain portfolio metrics clearly and simply.",
            user_prompt=f"""
Analyze these portfolio metrics and explain what they mean:

Portfolio Metrics:
- Volatility: {metrics['volatility']}%
- Expected Return: {metrics['avg_return']}%
- Sharpe Ratio: {metrics['sharpe_ratio']}

Holdings analyzed: {list(holdings_dict.keys())}

Question: {user_message}

Provide a clear, beginner-friendly explanation of what these metrics tell us about portfolio risk.
            """,
            temperature=0.3
        )
        return explanation
    
    except Exception as e:
        logger.error(f"Error in risk profiler LLM: {e}")
        return f"Risk Profile - Volatility: {metrics['volatility']}%, Return: {metrics['avg_return']}%, Sharpe Ratio: {metrics['sharpe_ratio']}"
