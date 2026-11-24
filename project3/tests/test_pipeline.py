import pandas as pd
from ridecast.pipeline import split_data


def test_chronological_split():
    config = {"split": {"train_end_exclusive": "2012-07-01",
                        "validation_end_exclusive": "2012-10-01",
                        "test_end_exclusive": "2013-01-01"}}
    df = pd.DataFrame({"timestamp": pd.to_datetime(
        ["2012-06-30", "2012-07-01", "2012-10-01"])})
    parts = split_data(df, config)
    assert list(map(len, parts.values())) == [1, 1, 1]
