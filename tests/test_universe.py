import pandas as pd
import pytest

from hedge_fund.universe import PointInTimeUniverse


def _membership_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "as_of_date": [
                "2018-01-01", "2018-01-01",
                "2020-01-01", "2020-01-01",
                "2022-01-01",
            ],
            "ticker": ["A", "B", "A", "C", "D"],
        }
    )


def test_members_on_returns_latest_snapshot_at_or_before_date():
    u = PointInTimeUniverse(_membership_df())
    assert u.members_on("2019-06-01") == {"A", "B"}
    assert u.members_on("2020-01-01") == {"A", "C"}
    assert u.members_on("2021-12-31") == {"A", "C"}
    assert u.members_on("2022-06-01") == {"D"}


def test_members_on_before_first_snapshot_is_empty():
    u = PointInTimeUniverse(_membership_df())
    assert u.members_on("2017-12-31") == set()


def test_mask_reflects_snapshots():
    u = PointInTimeUniverse(_membership_df())
    dates = pd.DatetimeIndex(["2019-06-01", "2020-06-01", "2022-06-01"])
    mask = u.mask(dates, ["A", "B", "C", "D"])
    assert mask.loc["2019-06-01"].to_dict() == {"A": True, "B": True, "C": False, "D": False}
    assert mask.loc["2020-06-01"].to_dict() == {"A": True, "B": False, "C": True, "D": False}
    assert mask.loc["2022-06-01"].to_dict() == {"A": False, "B": False, "C": False, "D": True}


def test_missing_required_columns_raises():
    with pytest.raises(ValueError, match="missing columns"):
        PointInTimeUniverse(pd.DataFrame({"as_of_date": ["2020-01-01"]}))


def test_sample_csv_loads():
    from pathlib import Path
    csv_path = Path(__file__).resolve().parent.parent / "data" / "sp500_membership_sample.csv"
    u = PointInTimeUniverse.from_csv(csv_path)
    assert len(u.snapshots) == 3
    assert "AAPL" in u.members_on("2018-06-01")
    assert "TSLA" not in u.members_on("2018-06-01")
    assert "TSLA" in u.members_on("2021-01-01")
