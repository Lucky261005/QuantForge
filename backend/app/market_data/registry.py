from app.market_data.alpha_vantage import AlphaVantageProvider
from app.market_data.angel_one import AngelOneProvider
from app.market_data.base import MarketDataProvider
from app.market_data.kite import KiteConnectProvider
from app.market_data.nse_official import NSEOfficialProvider
from app.market_data.polygon import PolygonProvider
from app.market_data.upstox import UpstoxProvider
from app.market_data.yahoo import YahooFinanceProvider
from app.models.market_data import DataSource

_PROVIDERS: dict[DataSource, type[MarketDataProvider]] = {
    DataSource.YAHOO_FINANCE: YahooFinanceProvider,
    DataSource.ALPHA_VANTAGE: AlphaVantageProvider,
    DataSource.POLYGON: PolygonProvider,
    DataSource.NSE_OFFICIAL: NSEOfficialProvider,
    DataSource.KITE_CONNECT: KiteConnectProvider,
    DataSource.UPSTOX: UpstoxProvider,
    DataSource.ANGEL_ONE: AngelOneProvider,
}


def get_provider(source: DataSource) -> MarketDataProvider:
    provider_cls = _PROVIDERS.get(source)
    if provider_cls is None:
        raise ValueError(f"No provider registered for source '{source}'")
    return provider_cls()
