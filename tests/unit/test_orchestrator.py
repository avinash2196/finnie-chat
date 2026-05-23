from unittest.mock import patch, AsyncMock


@patch('app.agents.orchestrator.observability.start_langsmith_run', return_value='rid')
@patch('app.agents.orchestrator.observability.end_langsmith_run')
async def test_planner_fallback_on_llm_error(mock_end, mock_start):
    from app.agents.orchestrator import handle_message

    with patch('app.agents.orchestrator.classify_intent', return_value=("ASK_MARKET", "LOW")), \
         patch('app.agents.orchestrator.acall_llm', new=AsyncMock(side_effect=Exception("planner fail"))), \
         patch('app.agents.orchestrator.market_run', return_value="Quote: 100"), \
         patch('app.agents.orchestrator.compliance_run', return_value="COMPL"), \
         patch('app.agents.orchestrator.get_portfolio_client') as mock_pc:
        mock_pc.return_value.get_holdings.return_value = {'holdings': {}}
        final, intent, risk = await handle_message("Price AAPL?", user_id="u1")
        assert intent == "ASK_MARKET"
        assert final == "COMPL"


async def test_ask_concept_guard_returns_when_no_educator():
    from app.agents.orchestrator import handle_message

    with patch('app.agents.orchestrator.classify_intent', return_value=("ASK_CONCEPT", "LOW")), \
         patch('app.agents.orchestrator.acall_llm', new=AsyncMock(side_effect=Exception("planner fail"))), \
         patch('app.agents.orchestrator.compliance_run', return_value="COMPL"), \
         patch('app.agents.orchestrator.educator_run', return_value=None), \
         patch('app.agents.orchestrator.get_portfolio_client') as mock_pc, \
         patch('app.agents.orchestrator.observability.start_langsmith_run', return_value='rid'), \
         patch('app.agents.orchestrator.observability.end_langsmith_run'):
        mock_pc.return_value.get_holdings.return_value = {'holdings': {}}
        resp = await handle_message("Explain ETFs", user_id="u1")
        assert isinstance(resp, tuple)
        assert "trusted information" in resp[0]


async def test_synthesis_fallback_constructs_from_agent_contexts():
    from app.agents.orchestrator import handle_message

    # acall_llm: first call returns planner json, second call (synthesis) raises
    acall_side_effects = ["{\"plan\": [\"MarketAgent\"]}", Exception("synth fail")]
    call_count = 0

    async def mock_acall_llm(*args, **kwargs):
        nonlocal call_count
        val = acall_side_effects[call_count]
        call_count += 1
        if isinstance(val, Exception):
            raise val
        return val

    with patch('app.agents.orchestrator.classify_intent', return_value=("ASK_MARKET", "LOW")), \
         patch('app.agents.orchestrator.acall_llm', side_effect=mock_acall_llm), \
         patch('app.agents.orchestrator.market_run', return_value="MarketOutput"), \
         patch('app.agents.orchestrator.compliance_run', return_value="COMPL"), \
         patch('app.agents.orchestrator.get_portfolio_client') as mock_pc, \
         patch('app.agents.orchestrator.observability.start_langsmith_run', return_value='rid'), \
         patch('app.agents.orchestrator.observability.end_langsmith_run'):
        mock_pc.return_value.get_holdings.return_value = {'holdings': {}}
        final, intent, risk = await handle_message("Price AAPL?", user_id="u1")
        assert final == "COMPL"
        assert intent == "ASK_MARKET"


async def test_final_compliance_invoked_and_returned():
    from app.agents.orchestrator import handle_message

    with patch('app.agents.orchestrator.classify_intent', return_value=("ASK_MARKET", "LOW")), \
         patch('app.agents.orchestrator.acall_llm', new=AsyncMock(return_value='{"plan": ["MarketAgent"]}')), \
         patch('app.agents.orchestrator.market_run', return_value="MarketOutput"), \
         patch('app.agents.orchestrator.compliance_run', return_value="SAFE"), \
         patch('app.agents.orchestrator.get_portfolio_client') as mock_pc, \
         patch('app.agents.orchestrator.observability.start_langsmith_run', return_value='rid'), \
         patch('app.agents.orchestrator.observability.end_langsmith_run'):
        mock_pc.return_value.get_holdings.return_value = {'holdings': {}}
        final, intent, risk = await handle_message("Price AAPL?", user_id="u1")
        assert final == "SAFE"
