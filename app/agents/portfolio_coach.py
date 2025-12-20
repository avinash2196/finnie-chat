"""Portfolio coach for holdings analysis and allocation optimization."""

from app.mcp.market import get_client
from app.mcp.portfolio import get_portfolio_client
from app.llm import call_llm
import logging

logger = logging.getLogger(__name__)


def analyze_allocation(holdings_dict):
    """Analyze portfolio allocation and calculate position sizes.
    
    Args:
        holdings_dict: {
            'AAPL': {'quantity': 10, 'purchase_price': 150},
            'MSFT': {'quantity': 5, 'purchase_price': 300}
        }
    
    Returns:
        dict with allocation percentages and total value
    """
    try:
        client = get_client()
        
        # Calculate current value of each position
        total_value = 0
        holdings_with_value = {}
        
        for ticker, holding in holdings_dict.items():
            quote = client.get_quote(ticker)
            if quote.price is None:
                logger.warning(f"Could not fetch price for {ticker}")
                return {
                    'error': f"Could not fetch price for {ticker}",
                    'allocation': {}
                }
            
            quantity = holding.get('quantity', 0)
            value = quantity * quote.price
            total_value += value
            holdings_with_value[ticker] = {
                'value': value,
                'quantity': quantity,
                'current_price': quote.price
            }
        
        # Calculate allocation percentages
        allocation = {}
        for ticker, data in holdings_with_value.items():
            pct = (data['value'] / total_value * 100) if total_value > 0 else 0
            allocation[ticker] = {
                'percentage': round(pct, 2),
                'value': round(data['value'], 2),
                'quantity': data['quantity'],
                'current_price': round(data['current_price'], 2)
            }
        
        return {
            'allocation': allocation,
            'total_value': round(total_value, 2),
            'error': None
        }
    
    except Exception as e:
        logger.error(f"Error analyzing allocation: {e}")
        return {
            'allocation': {},
            'total_value': 0,
            'error': str(e)
        }


def detect_concentration(allocation):
    """Detect if portfolio is too concentrated in one position.
    
    Args:
        allocation: dict with ticker: {'percentage': pct, ...}
    
    Returns:
        tuple (is_concentrated, max_allocation_pct, concentrated_tickers)
    """
    if not allocation:
        return False, 0, []
    
    percentages = [data['percentage'] for data in allocation.values()]
    max_pct = max(percentages) if percentages else 0
    
    # Define concentration thresholds
    is_concentrated = max_pct >= 40  # >=40% is concentrated
    concentrated_tickers = [
        ticker for ticker, data in allocation.items()
        if data['percentage'] >= 30
    ]
    
    return is_concentrated, round(max_pct, 2), concentrated_tickers


def calculate_diversification_score(allocation):
    """Calculate diversification score (0-100).
    
    Args:
        allocation: dict with ticker: {'percentage': pct, ...}
    
    Returns:
        float: diversification score (0=single holding, 100=perfectly equal weights)
    """
    if not allocation:
        return 0
    
    n = len(allocation)
    if n == 1:
        return 0  # Single holding = no diversification
    
    # For N holdings, ideal allocation is 100/N percent each
    ideal_allocation = 100 / n
    
    # Calculate how far from ideal each position is
    variance = sum(
        (data['percentage'] - ideal_allocation) ** 2
        for data in allocation.values()
    ) / n
    
    # Convert variance to 0-100 scale (lower variance = higher score)
    # For N holdings, theoretical max variance is when heavily concentrated
    max_variance = ((100 - ideal_allocation) ** 2 + (n - 1) * (ideal_allocation ** 2)) / n
    
    if max_variance > 0:
        diversification_score = max(0, 100 - (variance / max_variance * 100))
    else:
        diversification_score = 100
    
    return round(diversification_score, 2)


def run(user_message: str, holdings_dict: dict = None, user_id: str = "user_123"):
    """Main portfolio coach agent.
    
    Args:
        user_message: User query or request
        holdings_dict: Portfolio holdings (deprecated, use user_id instead)
        user_id: User identifier to fetch portfolio from MCP
    
    Returns:
        str: LLM-generated recommendations
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
        return "No holdings to analyze. Please provide your portfolio holdings."
    
    # Analyze allocation
    result = analyze_allocation(holdings_dict)
    if result['error']:
        return f"Error analyzing portfolio: {result['error']}"
    
    allocation = result['allocation']
    total_value = result['total_value']
    
    # Detect concentration
    is_concentrated, max_pct, concentrated_tickers = detect_concentration(allocation)
    
    # Calculate diversification score
    diversification_score = calculate_diversification_score(allocation)
    
    # Format allocation for LLM
    allocation_text = "\n".join([
        f"  {ticker}: {data['percentage']}% (${data['value']:,.2f})"
        for ticker, data in allocation.items()
    ])
    
    # Generate recommendations using LLM
    try:
        recommendations = call_llm(
            system_prompt="You are an experienced investment portfolio advisor with expertise in diversification and risk management.",
            user_prompt=f"""
            Analyze this portfolio allocation:
            
            Total Portfolio Value: ${total_value:,.2f}
            
            Current Allocation:
            {allocation_text}
            
            Portfolio Metrics:
            - Diversification Score: {diversification_score}/100
            - Maximum Position: {max_pct}%
            - Number of Holdings: {len(allocation)}
            
            Concentration Issues:
            - Is Concentrated (>40% in single position): {'Yes' if is_concentrated else 'No'}
            {'- Concentrated Positions (>30%): ' + ', '.join(concentrated_tickers) if concentrated_tickers else ''}
            
            User Query: {user_message}
            
            Please provide:
            1. Assessment of current diversification
            2. Specific risks based on concentration
            3. Actionable recommendations for rebalancing
            4. Suggested target allocations if applicable
            
            Be concise and practical in your recommendations.
            """
        )
        return recommendations
    
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        # Fallback response with metrics
        return f"""
Portfolio Allocation Analysis:

{allocation_text}

Total Value: ${total_value:,.2f}
Diversification Score: {diversification_score}/100
Maximum Position: {max_pct}%

Summary: Your portfolio has {len(allocation)} holdings. 
{'This portfolio is concentrated - consider rebalancing to reduce risk.' if is_concentrated else 'Your portfolio appears reasonably diversified.'}
"""
