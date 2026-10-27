import pytest

from app.market_data.registry import get_provider
from app.market_data.yahoo import _to_yahoo_symbol
from app.models.market_data import DataSource


@pytest.mark.parametrize(
    "symbol,expected",
    [
        ("RELIANCE", "RELIANCE.NS"),
        ("TCS", "TCS.NS"),
        ("RELIANCE.BO", "RELIANCE.BO"),
        ("RELIANCE.NS", "RELIANCE.NS"),
        ("^NSEI", "^NSEI"),
        ("^BSESN", "^BSESN"),
    ],
)
def test_to_yahoo_symbol_appends_ns_suffix_by_default(symbol: str, expected: str):
    assert _to_yahoo_symbol(symbol) == expected


@pytest.mark.parametrize(
    "source",
    [
        DataSource.YAHOO_FINANCE,
        DataSource.ALPHA_VANTAGE,
        DataSource.POLYGON,
        DataSource.NSE_OFFICIAL,
        DataSource.KITE_CONNECT,
        DataSource.UPSTOX,
        DataSource.ANGEL_ONE,
    ],
)
def test_every_data_source_has_a_registered_provider(source: DataSource):
    provider = get_provider(source)
    assert provider.name

    assert provider.is_configured() is not None  # must not raise; True/False either is valid


def test_indian_broker_providers_are_unconfigured_without_credentials():
    for source in (DataSource.KITE_CONNECT, DataSource.UPSTOX, DataSource.ANGEL_ONE):
        assert get_provider(source).is_configured() is False
