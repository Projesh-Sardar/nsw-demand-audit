"""
Audit checks for a daily or half-hourly time series.

This is the core of the project. The point is not to produce a model — it is
to find out what is wrong with the data before anyone models it.

Every function here answers one question and prints what it found. Read the
output, then decide what it means. Do not skip to the modelling.

Usage:
    python audit.py data/weather_sydney.csv date
    python audit.py data/demand_nsw.csv SETTLEMENTDATE
"""

import sys

import pandas as pd


def load(path: str, time_col: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df[time_col] = pd.to_datetime(df[time_col])
    return df.sort_values(time_col).reset_index(drop=True)


def check_gaps(df: pd.DataFrame, time_col: str) -> None:
    """Are any time steps missing entirely?

    A missing row is not the same as a row with a missing value, and most
    analyses silently treat them differently.
    """
    print("\n--- GAPS ---")
    deltas = df[time_col].diff().dropna()
    if deltas.empty:
        print("Not enough rows to check.")
        return

    expected = deltas.mode()[0]
    print(f"Most common interval: {expected}")

    odd = deltas[deltas != expected]
    print(f"Intervals that differ from it: {len(odd)}")
    if len(odd):
        print("First 10:")
        for idx, gap in odd.head(10).items():
            print(f"  after {df.loc[idx - 1, time_col]}: gap of {gap}")


def check_duplicates(df: pd.DataFrame, time_col: str) -> None:
    """Is any timestamp present more than once?

    In Australian data this is often the daylight saving rollback in April,
    where 2am happens twice. Worth knowing before you average anything.
    """
    print("\n--- DUPLICATE TIMESTAMPS ---")
    dupes = df[df.duplicated(time_col, keep=False)]
    print(f"Rows with a repeated timestamp: {len(dupes)}")
    if len(dupes):
        print(dupes.head(10).to_string())


def check_missing(df: pd.DataFrame) -> None:
    """Where are the nulls, and are they spread evenly or clustered?

    Clustered nulls usually mean something broke for a period. Evenly spread
    nulls usually mean something else. They need different treatment.
    """
    print("\n--- MISSING VALUES ---")
    nulls = df.isna().sum()
    nulls = nulls[nulls > 0]
    if nulls.empty:
        print("No nulls.")
        return
    print(nulls.to_string())

    for col in nulls.index:
        by_year = df[df[col].isna()].iloc[:, 0].dt.year.value_counts().sort_index()
        print(f"\n  {col} — nulls by year:")
        print("   " + by_year.to_string().replace("\n", "\n   "))


def check_outliers(df: pd.DataFrame, cols: list[str]) -> None:
    """Values far outside the usual range.

    Do not delete these. Find out what they are. A -9999 is a sentinel value
    someone used for 'missing'; a genuine 47 degree day is a real event and
    probably the most interesting row in the dataset.
    """
    print("\n--- OUTLIERS ---")
    for col in cols:
        if col not in df.columns or not pd.api.types.is_numeric_dtype(df[col]):
            continue
        s = df[col].dropna()
        if s.empty:
            continue
        q1, q3 = s.quantile([0.25, 0.75])
        iqr = q3 - q1
        lo, hi = q1 - 3 * iqr, q3 + 3 * iqr
        far = s[(s < lo) | (s > hi)]
        print(f"\n  {col}: range {s.min():.2f} to {s.max():.2f}, "
              f"{len(far)} values beyond 3x IQR")
        if len(far):
            print(f"    most extreme: {far.abs().nlargest(5).index.tolist()}")
            print(f"    values: {s.loc[far.abs().nlargest(5).index].tolist()}")


def check_flatlines(df: pd.DataFrame, cols: list[str], n: int = 4) -> None:
    """Runs of an identical value.

    A sensor that has failed often keeps reporting its last reading. That
    looks like data and is not.
    """
    print(f"\n--- FLATLINES (runs of {n}+ identical values) ---")
    for col in cols:
        if col not in df.columns or not pd.api.types.is_numeric_dtype(df[col]):
            continue
        s = df[col]
        grp = (s != s.shift()).cumsum()
        runs = s.groupby(grp).agg(["size", "first"])
        long_runs = runs[runs["size"] >= n]
        print(f"  {col}: {len(long_runs)} runs")
        if len(long_runs):
            print(f"    longest: {long_runs['size'].max()} repeats "
                  f"of value {long_runs.loc[long_runs['size'].idxmax(), 'first']}")


def check_stability(df: pd.DataFrame, time_col: str, cols: list[str]) -> None:
    """Does the series behave the same way across the whole period?

    A jump in mean or variance between years usually means a definitional
    change, a new instrument, or a different collection method — not a real
    change in the world. This is the check most people skip.
    """
    print("\n--- YEAR-ON-YEAR STABILITY ---")
    for col in cols:
        if col not in df.columns or not pd.api.types.is_numeric_dtype(df[col]):
            continue
        by_year = df.groupby(df[time_col].dt.year)[col].agg(["count", "mean", "std"])
        print(f"\n  {col}:")
        print("   " + by_year.round(2).to_string().replace("\n", "\n   "))


def main() -> None:
    path = sys.argv[1]
    time_col = sys.argv[2] if len(sys.argv) > 2 else "date"

    df = load(path, time_col)
    numeric = [c for c in df.columns
               if c != time_col and pd.api.types.is_numeric_dtype(df[c])]

    print(f"Loaded {path}")
    print(f"{len(df)} rows, {df[time_col].min()} to {df[time_col].max()}")
    print(f"Numeric columns: {numeric}")

    check_gaps(df, time_col)
    check_duplicates(df, time_col)
    check_missing(df)
    check_outliers(df, numeric)
    check_flatlines(df, numeric)
    check_stability(df, time_col, numeric)

    print("\n" + "=" * 60)
    print("Now write down, for each thing above: what it is, why you think")
    print("it happened, and whether it changes what the data can be used for.")
    print("That write-up is the project. The checks are just how you get there.")


if __name__ == "__main__":
    main()
