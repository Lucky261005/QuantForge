"""Indian equity transaction cost model — statutory charges are regulator-set (SEBI/
exchange circulars), not user-configurable, so only brokerage is a free parameter here.
Rates below reflect NSE cash-equity charges as commonly published; review against the
current NSE/SEBI circular before relying on them for live capital allocation.

This sits alongside the existing flat `commission_pct`/`slippage_pct` model in
`app/backtesting/engine.py` — `ChargeModel.FLAT` preserves that behavior exactly.
"""

from dataclasses import dataclass
from enum import StrEnum


class ChargeModel(StrEnum):
    FLAT = "flat"
    INDIAN_EQUITY_DELIVERY = "indian_equity_delivery"
    INDIAN_EQUITY_INTRADAY = "indian_equity_intraday"


@dataclass(frozen=True, slots=True)
class IndianChargesConfig:
    brokerage_pct: float = 0.0  # discount brokers commonly charge ₹0 (or a flat fee, out of scope here) on delivery
    stt_delivery_pct: float = 0.001  # STT: 0.1% on both buy and sell, delivery
    stt_intraday_sell_pct: float = 0.00025  # STT: 0.025% on sell side only, intraday
    exchange_txn_charge_pct: float = 0.0000297  # NSE transaction charges, both sides
    sebi_charges_pct: float = 0.000001  # SEBI turnover fee: Rs 10 per crore, both sides
    stamp_duty_delivery_buy_pct: float = 0.00015  # stamp duty: 0.015% on buy side only, delivery
    stamp_duty_intraday_buy_pct: float = 0.00003  # stamp duty: 0.003% on buy side only, intraday
    gst_pct: float = 0.18  # GST on (brokerage + exchange transaction charges), both sides


def compute_entry_exit_cost_pct(charges: IndianChargesConfig, delivery: bool) -> tuple[float, float]:
    """Returns (entry_pct, exit_pct) — the total cost fraction charged on the buy leg and
    sell leg respectively, for a round-trip trade under Indian cash-equity charges.

    STT and stamp duty are asymmetric (delivery: STT on both legs, stamp duty on buy only;
    intraday: STT on sell only, stamp duty on buy only), so entry/exit costs genuinely
    differ and must be modeled separately rather than as one blended commission rate.
    """
    gst_on_brokerage_and_exchange = charges.gst_pct * (charges.brokerage_pct + charges.exchange_txn_charge_pct)
    base_pct = charges.brokerage_pct + charges.exchange_txn_charge_pct + charges.sebi_charges_pct
    base_pct += gst_on_brokerage_and_exchange

    if delivery:
        entry_pct = base_pct + charges.stt_delivery_pct + charges.stamp_duty_delivery_buy_pct
        exit_pct = base_pct + charges.stt_delivery_pct
    else:
        entry_pct = base_pct + charges.stamp_duty_intraday_buy_pct
        exit_pct = base_pct + charges.stt_intraday_sell_pct

    return entry_pct, exit_pct
