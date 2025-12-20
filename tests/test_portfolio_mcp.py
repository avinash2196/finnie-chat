"""Unit and integration tests for Portfolio MCP Server."""

import pytest
from datetime import datetime, timedelta
from app.mcp.portfolio import (
    get_user_holdings,
    get_user_profile,
    record_transaction,
    get_transaction_history,
    get_dividend_history,
    get_performance_metrics,
    get_portfolio_client,
    PortfolioClient
)


class TestGetUserHoldings:
    """Test get_user_holdings function."""
    
    def test_get_holdings_existing_user(self):
        """Test getting holdings for existing user."""
        result = get_user_holdings("user_123")
        
        assert result['error'] is None
        assert result['user_id'] == "user_123"
        assert len(result['holdings']) > 0
        assert 'AAPL' in result['holdings']
        assert 'total_portfolio_value' in result
    
    def test_get_holdings_with_calculations(self):
        """Test that holdings include current value and gain/loss."""
        result = get_user_holdings("user_123")
        
        aapl = result['holdings']['AAPL']
        assert 'current_value' in aapl
        assert 'gain_loss' in aapl
        assert 'gain_loss_pct' in aapl
        # Purchase price was 150, current should be 180 (positive gain)
        assert aapl['gain_loss'] > 0
    
    def test_get_holdings_nonexistent_user(self):
        """Test getting holdings for nonexistent user."""
        result = get_user_holdings("nonexistent_user")
        
        assert result['error'] is not None
        assert result['holdings'] == {}
        assert result['total_portfolio_value'] == 0
    
    def test_get_holdings_total_calculation(self):
        """Test that totals are calculated correctly."""
        result = get_user_holdings("user_123")
        
        # Verify total_portfolio_value = total_shares_value + total_cash
        expected_total = result['total_shares_value'] + result['total_cash']
        assert result['total_portfolio_value'] == expected_total
    
    def test_get_holdings_multiple_stocks(self):
        """Test that all holdings are returned."""
        result = get_user_holdings("user_123")
        
        holdings = result['holdings']
        expected_tickers = ['AAPL', 'MSFT', 'GOOGL', 'JNJ', 'TSLA']
        for ticker in expected_tickers:
            assert ticker in holdings


class TestGetUserProfile:
    """Test get_user_profile function."""
    
    def test_get_profile_existing_user(self):
        """Test getting profile for existing user."""
        result = get_user_profile("user_123")
        
        assert result['error'] is None
        assert result['user_id'] == "user_123"
        assert result['profile'] is not None
    
    def test_get_profile_contains_expected_fields(self):
        """Test that profile contains expected fields."""
        result = get_user_profile("user_123")
        
        profile = result['profile']
        assert 'user_id' in profile
        assert 'name' in profile
        assert 'risk_tolerance' in profile
        assert 'investment_horizon' in profile
        assert 'investment_goals' in profile
        assert 'max_single_position' in profile
    
    def test_get_profile_nonexistent_user(self):
        """Test getting profile for nonexistent user."""
        result = get_user_profile("nonexistent_user")
        
        assert result['error'] is not None
        assert result['profile'] is None
    
    def test_get_profile_risk_tolerance_values(self):
        """Test that risk tolerance has valid value."""
        result = get_user_profile("user_123")
        
        risk_tolerance = result['profile']['risk_tolerance']
        assert risk_tolerance in ['conservative', 'moderate', 'aggressive']


class TestRecordTransaction:
    """Test record_transaction function."""
    
    def test_record_buy_transaction(self):
        """Test recording a buy transaction."""
        result = record_transaction("user_123", "NEW_TICKER", "buy", 10, 50.0, "Test buy")
        
        assert result['error'] is None
        assert result['transaction']['type'] == "buy"
        assert result['transaction']['ticker'] == "NEW_TICKER"
        assert result['transaction']['quantity'] == 10
        assert result['transaction']['amount'] == 500.0
    
    def test_record_sell_transaction(self):
        """Test recording a sell transaction."""
        result = record_transaction("user_123", "AAPL", "sell", 10, 180.0, "Test sell")
        
        assert result['error'] is None
        assert result['transaction']['type'] == "sell"
        assert result['transaction']['amount'] == 1800.0
    
    def test_record_dividend_transaction(self):
        """Test recording a dividend transaction."""
        result = record_transaction("user_123", "JNJ", "dividend", 1, 240.0, "Q4 dividend")
        
        assert result['error'] is None
        assert result['transaction']['type'] == "dividend"
        assert result['transaction']['amount'] == 240.0
    
    def test_record_invalid_transaction_type(self):
        """Test error on invalid transaction type."""
        result = record_transaction("user_123", "TEST", "invalid_type", 10, 50.0)
        
        assert result['error'] is not None
    
    def test_record_transaction_updates_holdings(self):
        """Test that recording buy updates holdings."""
        # Record a buy
        record_transaction("user_123", "TEST_STOCK", "buy", 5, 100.0)
        
        # Check holdings were updated
        holdings = get_user_holdings("user_123")
        assert 'TEST_STOCK' in holdings['holdings']
        assert holdings['holdings']['TEST_STOCK']['quantity'] == 5
    
    def test_record_transaction_generates_id(self):
        """Test that transactions get unique IDs."""
        result1 = record_transaction("user_123", "TICK1", "buy", 1, 100.0)
        result2 = record_transaction("user_123", "TICK2", "buy", 1, 100.0)
        
        assert result1['transaction']['id'] != result2['transaction']['id']


class TestGetTransactionHistory:
    """Test get_transaction_history function."""
    
    def test_get_all_transactions(self):
        """Test getting all transactions."""
        result = get_transaction_history("user_123")
        
        assert result['error'] is None
        assert result['user_id'] == "user_123"
        assert result['total_transactions'] > 0
        assert len(result['transactions']) == result['total_transactions']
    
    def test_transactions_sorted_by_date(self):
        """Test that transactions are sorted by date (newest first)."""
        result = get_transaction_history("user_123")
        
        transactions = result['transactions']
        if len(transactions) > 1:
            for i in range(len(transactions) - 1):
                assert transactions[i]['date'] >= transactions[i+1]['date']
    
    def test_filter_by_days(self):
        """Test filtering transactions by days."""
        result = get_transaction_history("user_123", days=30)
        
        assert result['error'] is None
        # Should have fewer or equal transactions than all-time
        result_all = get_transaction_history("user_123")
        assert len(result['transactions']) <= len(result_all['transactions'])
    
    def test_filter_by_type(self):
        """Test filtering transactions by type."""
        result = get_transaction_history("user_123", transaction_type="dividend")
        
        assert result['error'] is None
        # All transactions should be dividends
        for txn in result['transactions']:
            assert txn['type'] == "dividend"
    
    def test_filter_by_days_and_type(self):
        """Test filtering by both days and type."""
        result = get_transaction_history("user_123", days=365, transaction_type="buy")
        
        assert result['error'] is None
        for txn in result['transactions']:
            assert txn['type'] == "buy"
    
    def test_nonexistent_user_transactions(self):
        """Test getting transactions for nonexistent user."""
        result = get_transaction_history("nonexistent_user")
        
        assert result['error'] is None
        assert result['total_transactions'] == 0


class TestGetDividendHistory:
    """Test get_dividend_history function."""
    
    def test_get_dividend_history(self):
        """Test getting dividend history."""
        result = get_dividend_history("user_123")
        
        assert result['error'] is None
        assert result['user_id'] == "user_123"
        assert 'total_dividends_period' in result
        assert 'dividends_by_ticker' in result
    
    def test_dividend_totals_calculated(self):
        """Test that dividend totals are calculated."""
        result = get_dividend_history("user_123", days=365)
        
        # Should have dividend data (JNJ has dividends in mock data)
        assert result['total_dividends_period'] > 0
    
    def test_dividend_by_ticker_breakdown(self):
        """Test dividend breakdown by ticker."""
        result = get_dividend_history("user_123", days=365)
        
        dividends_by_ticker = result['dividends_by_ticker']
        if dividends_by_ticker:
            for ticker, data in dividends_by_ticker.items():
                assert 'total_amount' in data
                assert 'transaction_count' in data
    
    def test_dividend_period_filtering(self):
        """Test that dividends are filtered by period."""
        result_1year = get_dividend_history("user_123", days=365)
        result_30days = get_dividend_history("user_123", days=30)
        
        # 30-day should have fewer or equal dividends
        assert len(result_30days['dividend_transactions']) <= len(result_1year['dividend_transactions'])


class TestGetPerformanceMetrics:
    """Test get_performance_metrics function."""
    
    def test_get_all_performance_metrics(self):
        """Test getting all performance metrics."""
        result = get_performance_metrics("user_123")
        
        assert result['error'] is None
        assert len(result['metrics']) > 0
        assert 'AAPL' in result['metrics']
    
    def test_get_specific_ticker_metrics(self):
        """Test getting metrics for specific ticker."""
        result = get_performance_metrics("user_123", ticker="AAPL")
        
        assert result['error'] is None
        assert result['ticker'] == "AAPL"
        metrics = result['metrics']
        assert 'current_price' in metrics
        assert 'prices_last_30_days' in metrics
        assert 'dividend_yield' in metrics
        assert '52week_high' in metrics
        assert '52week_low' in metrics
    
    def test_ticker_not_found(self):
        """Test error when ticker not found."""
        result = get_performance_metrics("user_123", ticker="NONEXISTENT")
        
        assert result['error'] is not None
    
    def test_user_no_performance_data(self):
        """Test error when user has no performance data."""
        result = get_performance_metrics("nonexistent_user")
        
        assert result['error'] is not None


class TestPortfolioClient:
    """Test PortfolioClient class."""
    
    def test_client_initialization(self):
        """Test creating a portfolio client."""
        client = PortfolioClient("user_123")
        
        assert client.user_id == "user_123"
    
    def test_client_get_holdings(self):
        """Test client get_holdings method."""
        client = PortfolioClient("user_123")
        result = client.get_holdings()
        
        assert result['error'] is None
        assert len(result['holdings']) > 0
    
    def test_client_get_profile(self):
        """Test client get_profile method."""
        client = PortfolioClient("user_123")
        result = client.get_profile()
        
        assert result['error'] is None
        assert result['profile'] is not None
    
    def test_client_get_transactions(self):
        """Test client get_transactions method."""
        client = PortfolioClient("user_123")
        result = client.get_transactions()
        
        assert result['error'] is None
        assert result['total_transactions'] > 0
    
    def test_client_get_dividends(self):
        """Test client get_dividends method."""
        client = PortfolioClient("user_123")
        result = client.get_dividends()
        
        assert result['error'] is None
        assert 'total_dividends_period' in result
    
    def test_client_get_performance(self):
        """Test client get_performance method."""
        client = PortfolioClient("user_123")
        result = client.get_performance()
        
        assert result['error'] is None
        assert len(result['metrics']) > 0
    
    def test_client_record_buy(self):
        """Test client record_buy method."""
        client = PortfolioClient("user_123")
        result = client.record_buy("BUY_TEST", 10, 50.0, "Client test")
        
        assert result['error'] is None
        assert result['transaction']['type'] == "buy"
    
    def test_client_record_sell(self):
        """Test client record_sell method."""
        client = PortfolioClient("user_123")
        result = client.record_sell("AAPL", 5, 180.0, "Client test")
        
        assert result['error'] is None
        assert result['transaction']['type'] == "sell"
    
    def test_client_record_dividend(self):
        """Test client record_dividend method."""
        client = PortfolioClient("user_123")
        result = client.record_dividend("JNJ", 240.0, "Client test")
        
        assert result['error'] is None
        assert result['transaction']['type'] == "dividend"


class TestGetPortfolioClientFactory:
    """Test get_portfolio_client factory function."""
    
    def test_factory_default_user(self):
        """Test getting default user client."""
        client = get_portfolio_client()
        
        assert client.user_id == "user_123"
    
    def test_factory_custom_user(self):
        """Test getting custom user client."""
        client = get_portfolio_client("custom_user")
        
        assert client.user_id == "custom_user"
    
    def test_factory_returns_client(self):
        """Test that factory returns PortfolioClient instance."""
        client = get_portfolio_client()
        
        assert isinstance(client, PortfolioClient)


class TestPortfolioIntegration:
    """Integration tests for portfolio MCP server."""
    
    def test_full_portfolio_workflow(self):
        """Test complete portfolio workflow."""
        # Get client
        client = get_portfolio_client("user_123")
        
        # Get profile
        profile = client.get_profile()
        assert profile['error'] is None
        
        # Get holdings
        holdings = client.get_holdings()
        assert holdings['error'] is None
        
        # Get transactions
        transactions = client.get_transactions()
        assert transactions['error'] is None
        
        # Get dividends
        dividends = client.get_dividends()
        assert dividends['error'] is None
        
        # Get performance
        performance = client.get_performance()
        assert performance['error'] is None
    
    def test_transaction_workflow(self):
        """Test transaction recording and retrieval."""
        client = get_portfolio_client("user_123")
        
        # Record a buy
        buy_result = client.record_buy("INTEGRATION_TEST", 100, 50.0, "Integration test buy")
        assert buy_result['error'] is None
        
        # Get transaction history
        history = client.get_transactions()
        assert history['error'] is None
        assert history['total_transactions'] > 0
        
        # Verify transaction is in history
        transaction_ids = [t['id'] for t in history['transactions']]
        assert buy_result['transaction']['id'] in transaction_ids
    
    def test_dividend_tracking(self):
        """Test dividend recording and tracking."""
        client = get_portfolio_client("user_123")
        
        # Record a dividend
        div_result = client.record_dividend("INTEGRATION_DIV", 100.0, "Integration test dividend")
        assert div_result['error'] is None
        
        # Get dividend history
        dividends = client.get_dividends(days=365)
        assert dividends['error'] is None
        
        # Find our dividend in history
        div_ids = [t['id'] for t in dividends['dividend_transactions']]
        assert div_result['transaction']['id'] in div_ids
    
    def test_performance_tracking_with_holdings(self):
        """Test that holdings and performance are consistent for core holdings."""
        client = get_portfolio_client("user_123")
        
        # Get holdings
        holdings = client.get_holdings()
        held_tickers = list(holdings['holdings'].keys())
        
        # Get performance
        performance = client.get_performance()
        performance_tickers = list(performance['metrics'].keys())
        
        # Check only core holdings (those in original mock data) have performance data
        core_tickers = ['AAPL', 'MSFT', 'GOOGL', 'JNJ', 'TSLA']
        for ticker in core_tickers:
            if ticker in held_tickers:
                assert ticker in performance_tickers, f"{ticker} in holdings but not in performance"
