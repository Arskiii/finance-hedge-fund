"""Point-in-time index membership.

Static-universe backtests (the prior `DEFAULT_UNIVERSE`) overstate returns by
silently selecting for survivors. This module restricts the investable set at
each rebalance to the names that were actually in the index on that date.

Membership is provided as a long-format table of (as_of_date, ticker)
snapshots. Each snapshot is a complete listing as of that date; the universe
on rebalance date `t` is the latest snapshot with `as_of_date <= t`.
"""
from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import pandas as pd


class PointInTimeUniverse:
    def __init__(self, memberships: pd.DataFrame) -> None:
        required = {"as_of_date", "ticker"}
        missing = required - set(memberships.columns)
        if missing:
            raise ValueError(f"memberships is missing columns: {sorted(missing)}")
        df = memberships[["as_of_date", "ticker"]].copy()
        df["as_of_date"] = pd.to_datetime(df["as_of_date"])
        self._memberships = df.sort_values("as_of_date").reset_index(drop=True)

    @classmethod
    def from_csv(cls, path: str | Path) -> PointInTimeUniverse:
        return cls(pd.read_csv(path))

    @property
    def all_tickers(self) -> list[str]:
        return sorted(self._memberships["ticker"].unique().tolist())

    @property
    def snapshots(self) -> list[pd.Timestamp]:
        return sorted(pd.DatetimeIndex(self._memberships["as_of_date"].unique()).tolist())

    def members_on(self, date: pd.Timestamp | str) -> set[str]:
        ts = pd.Timestamp(date)
        snaps = [s for s in self.snapshots if s <= ts]
        if not snaps:
            return set()
        latest = snaps[-1]
        rows = self._memberships[self._memberships["as_of_date"] == latest]
        return set(rows["ticker"])

    def mask(
        self,
        dates: Iterable[pd.Timestamp],
        tickers: Iterable[str],
    ) -> pd.DataFrame:
        """Boolean DataFrame: rows=dates, columns=tickers, True iff in universe."""
        date_index = pd.DatetimeIndex(list(dates))
        cols = list(tickers)
        out = pd.DataFrame(False, index=date_index, columns=cols)
        for d in date_index:
            members = self.members_on(d)
            out.loc[d] = [t in members for t in cols]
        return out
