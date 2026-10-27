"""One-off: mark demo data seeded before the `synthetic` data source existed.

Older runs of seed_demo_data.py stored their generated prices as `csv_upload`. This
relabels those bars as `synthetic` so the app shows them as synthetic demo data. Only
the `source` column of the seeded symbols changes; no prices or rows are touched.

Run from backend/ with the app's environment (uses DATABASE_URL):
    python ../scripts/relabel_synthetic_demo_data.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from sqlalchemy import select, update  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
from app.models.asset import Asset  # noqa: E402
from app.models.market_data import DataSource, MarketData  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_demo_data import INDICES, STOCKS  # noqa: E402

SEEDED_SYMBOLS = [*STOCKS, *INDICES]


def main() -> None:
    with SessionLocal() as db:
        asset_ids = list(db.scalars(select(Asset.id).where(Asset.symbol.in_(SEEDED_SYMBOLS))))
        result = db.execute(
            update(MarketData)
            .where(MarketData.asset_id.in_(asset_ids), MarketData.source == DataSource.CSV_UPLOAD)
            .values(source=DataSource.SYNTHETIC)
        )
        db.commit()
        print(f"Relabelled {result.rowcount} bars across {len(asset_ids)} seeded symbols as synthetic.")


if __name__ == "__main__":
    main()
