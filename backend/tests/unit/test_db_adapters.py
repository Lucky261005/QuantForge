"""NumPy scalars must reach PostgreSQL as plain numbers (NumPy 2's repr is "np.float64(...)")."""

import numpy as np
from psycopg2.extensions import adapt

import app.db.session  # noqa: F401 — registers the adapters


def test_numpy_scalars_adapt_to_plain_sql_numbers():
    assert adapt(np.float64(1.5)).getquoted() == b"1.5"
    assert adapt(np.float32(2.0)).getquoted() == b"2.0"
    assert adapt(np.int64(7)).getquoted() == b"7"
    assert adapt(np.float64("nan")).getquoted() == b"'NaN'::float"
