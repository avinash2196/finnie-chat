from unittest.mock import patch
from fastapi.testclient import TestClient
from types import SimpleNamespace
import app.main as mainmod

class DummyClient:
    def get_quotes(self, symbols):
        return {s.upper(): SimpleNamespace(price=100.0 if s.upper()=="AAPL" else 200.0, change_pct=1.5, currency="USD") for s in symbols}

mainmod._quote_agg_cache.clear()
mainmod._redis_client = None

with patch('app.main.get_client', return_value=DummyClient()):
    client = TestClient(mainmod.app)
    resp = client.post('/market/quote', json={'symbols': ['AAPL','MSFT']})
    print('STATUS', resp.status_code)
    print('BODY', resp.json())
