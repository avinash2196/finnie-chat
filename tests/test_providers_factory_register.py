from app.providers import PortfolioProviderFactory, PortfolioProvider


class DummyProvider(PortfolioProvider):
    async def get_holdings(self, user_id, credentials):
        return []

    async def get_transactions(self, user_id, credentials):
        return []

    async def get_current_prices(self, tickers):
        return {t: 0.0 for t in tickers}


def test_register_and_get_custom_provider():
    PortfolioProviderFactory.register_provider("dummy", DummyProvider)
    p = PortfolioProviderFactory.get_provider("dummy")
    assert isinstance(p, DummyProvider)
