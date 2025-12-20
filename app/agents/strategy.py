"""Strategy agent for investment screening and recommendations."""

from app.mcp.market import get_client
from app.llm import call_llm
import logging

logger = logging.getLogger(__name__)


def run_dividend_screener(holdings_dict):
    """Screen for dividend opportunities in portfolio.
    
    Args:
        holdings_dict: {
            'AAPL': {'quantity': 10, 'purchase_price': 150},
            'MSFT': {'quantity': 5, 'purchase_price': 300}
        }
    
    Returns:
        dict with dividend analysis
    """
    try:
        client = get_client()
        
        dividend_opportunities = []
        
        for ticker, holding in holdings_dict.items():
            try:
                quote = client.get_quote(ticker)
                if quote.price is None:
                    logger.warning(f"Could not fetch data for {ticker}")
                    continue
                
                # Get dividend info (if available in quote)
                # Note: This is simplified - in production would fetch from financial API
                dividend_yield = getattr(quote, 'dividend_yield', 0) or 0
                
                quantity = holding.get('quantity', 0)
                current_value = quantity * quote.price
                
                dividend_opportunities.append({
                    'ticker': ticker,
                    'current_price': round(quote.price, 2),
                    'quantity': quantity,
                    'position_value': round(current_value, 2),
                    'dividend_yield': round(dividend_yield, 2),
                    'annual_income': round(current_value * (dividend_yield / 100), 2) if dividend_yield else 0
                })
            
            except Exception as e:
                logger.error(f"Error processing {ticker} for dividend screening: {e}")
                continue
        
        return {
            'error': None,
            'opportunities': dividend_opportunities,
            'total_dividend_income': round(
                sum(opp['annual_income'] for opp in dividend_opportunities), 2
            )
        }
    
    except Exception as e:
        logger.error(f"Error running dividend screener: {e}")
        return {
            'error': str(e),
            'opportunities': [],
            'total_dividend_income': 0
        }


def run_growth_screener(holdings_dict, min_growth_rate=15):
    """Screen for growth opportunities.
    
    Looks for stocks with:
    - Positive recent performance
    - Potential for capital appreciation
    
    Args:
        holdings_dict: Portfolio holdings
        min_growth_rate: Minimum expected annual growth (%)
    
    Returns:
        dict with growth analysis
    """
    try:
        client = get_client()
        
        growth_candidates = []
        
        for ticker, holding in holdings_dict.items():
            try:
                quote = client.get_quote(ticker)
                if quote.price is None:
                    continue
                
                purchase_price = holding.get('purchase_price', 0)
                current_price = quote.price
                
                if purchase_price > 0:
                    # Calculate current return
                    current_return = ((current_price - purchase_price) / purchase_price) * 100
                    
                    quantity = holding.get('quantity', 0)
                    position_value = quantity * current_price
                    unrealized_gain = quantity * (current_price - purchase_price)
                    
                    # Check if growth candidate
                    is_growth_candidate = current_return > 0  # Positive momentum
                    
                    growth_candidates.append({
                        'ticker': ticker,
                        'current_price': round(current_price, 2),
                        'purchase_price': round(purchase_price, 2),
                        'current_return': round(current_return, 2),
                        'quantity': quantity,
                        'position_value': round(position_value, 2),
                        'unrealized_gain': round(unrealized_gain, 2),
                        'is_growth_candidate': is_growth_candidate
                    })
            
            except Exception as e:
                logger.error(f"Error processing {ticker} for growth screening: {e}")
                continue
        
        # Filter for actual growth candidates
        top_performers = [c for c in growth_candidates if c['is_growth_candidate']]
        top_performers.sort(key=lambda x: x['current_return'], reverse=True)
        
        return {
            'error': None,
            'all_holdings': growth_candidates,
            'top_performers': top_performers[:3],  # Top 3 growth stocks
            'total_unrealized_gains': round(
                sum(c['unrealized_gain'] for c in growth_candidates), 2
            )
        }
    
    except Exception as e:
        logger.error(f"Error running growth screener: {e}")
        return {
            'error': str(e),
            'all_holdings': [],
            'top_performers': [],
            'total_unrealized_gains': 0
        }


def run_value_screener(holdings_dict):
    """Screen for undervalued opportunities.
    
    Looks for stocks with:
    - Below purchase price (potential bargains)
    - Solid fundamentals
    
    Args:
        holdings_dict: Portfolio holdings
    
    Returns:
        dict with value analysis
    """
    try:
        client = get_client()
        
        undervalued_stocks = []
        
        for ticker, holding in holdings_dict.items():
            try:
                quote = client.get_quote(ticker)
                if quote.price is None:
                    continue
                
                purchase_price = holding.get('purchase_price', 0)
                current_price = quote.price
                
                if purchase_price > 0:
                    # Calculate discount
                    discount_pct = ((purchase_price - current_price) / purchase_price) * 100
                    
                    quantity = holding.get('quantity', 0)
                    position_value = quantity * current_price
                    unrealized_loss = quantity * (current_price - purchase_price)
                    
                    # Check if undervalued
                    is_undervalued = current_price < purchase_price
                    
                    undervalued_stocks.append({
                        'ticker': ticker,
                        'current_price': round(current_price, 2),
                        'purchase_price': round(purchase_price, 2),
                        'discount_pct': round(discount_pct, 2),
                        'quantity': quantity,
                        'position_value': round(position_value, 2),
                        'unrealized_loss': round(unrealized_loss, 2),
                        'is_undervalued': is_undervalued,
                        'potential_recovery': round(unrealized_loss * -1, 2) if unrealized_loss < 0 else 0
                    })
            
            except Exception as e:
                logger.error(f"Error processing {ticker} for value screening: {e}")
                continue
        
        # Filter for actual undervalued stocks
        bargains = [s for s in undervalued_stocks if s['is_undervalued']]
        bargains.sort(key=lambda x: x['discount_pct'], reverse=True)  # Biggest discounts first
        
        return {
            'error': None,
            'all_holdings': undervalued_stocks,
            'bargain_opportunities': bargains[:3],  # Top 3 bargains
            'total_unrealized_loss': round(
                sum(s['unrealized_loss'] for s in undervalued_stocks), 2
            )
        }
    
    except Exception as e:
        logger.error(f"Error running value screener: {e}")
        return {
            'error': str(e),
            'all_holdings': [],
            'bargain_opportunities': [],
            'total_unrealized_loss': 0
        }


def run(user_message: str, holdings_dict: dict = None, strategy_type: str = "balanced"):
    """Main strategy agent.
    
    Provides investment strategy recommendations based on:
    - Dividend yield optimization
    - Growth stock identification
    - Value investment opportunities
    
    Args:
        user_message: User query or request
        holdings_dict: Portfolio holdings
        strategy_type: "dividend", "growth", "value", or "balanced"
    
    Returns:
        str: LLM-generated strategy recommendations
    """
    if not holdings_dict:
        return "No holdings to analyze. Please provide your portfolio holdings."
    
    if not strategy_type or strategy_type not in ["dividend", "growth", "value", "balanced"]:
        strategy_type = "balanced"
    
    # Run appropriate screeners based on strategy type
    if strategy_type == "dividend":
        screening_results = run_dividend_screener(holdings_dict)
    elif strategy_type == "growth":
        screening_results = run_growth_screener(holdings_dict)
    elif strategy_type == "value":
        screening_results = run_value_screener(holdings_dict)
    else:  # balanced
        # Run all three screeners
        dividend_results = run_dividend_screener(holdings_dict)
        growth_results = run_growth_screener(holdings_dict)
        value_results = run_value_screener(holdings_dict)
        screening_results = {
            'dividend': dividend_results,
            'growth': growth_results,
            'value': value_results
        }
    
    # Format screening data for LLM
    if strategy_type == "balanced":
        screening_text = f"""
DIVIDEND STRATEGY:
- Total Annual Dividend Income: ${screening_results['dividend']['total_dividend_income']:,.2f}
- Opportunities: {len(screening_results['dividend']['opportunities'])} stocks with dividends

GROWTH STRATEGY:
- Top Performers: {len(screening_results['growth']['top_performers'])} growth stocks
- Total Unrealized Gains: ${screening_results['growth']['total_unrealized_gains']:,.2f}

VALUE STRATEGY:
- Bargain Opportunities: {len(screening_results['value']['bargain_opportunities'])} undervalued stocks
- Total Unrealized Loss: ${screening_results['value']['total_unrealized_loss']:,.2f}
"""
    else:
        # Single strategy format
        if strategy_type == "dividend":
            screening_text = f"""
DIVIDEND OPPORTUNITIES:
- Total Annual Dividend Income: ${screening_results['total_dividend_income']:,.2f}
- Opportunities Found: {len(screening_results['opportunities'])}
- Holdings with Dividends: {', '.join(o['ticker'] for o in screening_results['opportunities'] if o['dividend_yield'] > 0) or 'None'}
"""
        elif strategy_type == "growth":
            top_performers_text = "\n".join([
                f"  {p['ticker']}: {p['current_return']}% return (${p['unrealized_gain']:,.2f})"
                for p in screening_results['top_performers']
            ])
            screening_text = f"""
GROWTH OPPORTUNITIES:
- Total Unrealized Gains: ${screening_results['total_unrealized_gains']:,.2f}
- Top Performers:
{top_performers_text or '  None'}
"""
        else:  # value
            bargains_text = "\n".join([
                f"  {b['ticker']}: {b['discount_pct']}% discount (potential recovery: ${b['potential_recovery']:,.2f})"
                for b in screening_results['bargain_opportunities']
            ])
            screening_text = f"""
VALUE OPPORTUNITIES:
- Total Unrealized Loss: ${screening_results['total_unrealized_loss']:,.2f}
- Bargain Opportunities:
{bargains_text or '  None'}
"""
    
    # Generate strategy recommendations using LLM
    try:
        recommendations = call_llm(
            system_prompt="You are an expert investment strategist with expertise in portfolio optimization, dividend investing, growth investing, and value investing.",
            user_prompt=f"""
            Based on the following screening results for the portfolio:
            
            {screening_text}
            
            User Query: {user_message}
            
            Strategy Type: {strategy_type}
            
            Please provide:
            1. Assessment of the current strategy alignment
            2. Key opportunities identified by the screening
            3. Risk considerations
            4. Specific actionable recommendations (add, hold, or consider rebalancing)
            5. Expected outcomes if recommendations are followed
            
            Be concise and practical. Focus on the most impactful changes.
            """
        )
        return recommendations
    
    except Exception as e:
        logger.error(f"Error generating strategy recommendations: {e}")
        # Fallback response with screening data
        return f"""
Strategy Analysis ({strategy_type.upper()}):

{screening_text}

Summary: The portfolio has been screened for {strategy_type} opportunities.
Review the opportunities above and consider your investment goals and risk tolerance
when deciding which recommendations to implement.
"""
