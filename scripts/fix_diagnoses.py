# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "loguru==0.7.3",
#     "pandas==2.2.3",
#     "python-dateutil==2.9.0.post0",
# ]
# [tool.uv]
# exclude-newer = "2025-07-30T00:00:00Z"
# ///

"""Correct some issues in the 2023-USZ-Hypopharynx-Larynx dataset.

Fixes the date of planning CT entries in the 2023-USZ-Hypopharynx-Larynx dataset and
add a negative `diagnostic_consensus` column to all N0 patients that have no involvement
information at all.
"""

import argparse
from datetime import timedelta
from pathlib import Path

import pandas as pd
from dateutil.parser import parse
from loguru import logger


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the script."""
    argparser = argparse.ArgumentParser(description=__doc__)
    argparser.add_argument("input", type=Path, help="Path to the input dataset")
    argparser.add_argument("output", type=Path, help="Path to the output dataset")
    argparser.add_argument(
        "--delta-days",
        type=int,
        default=30,
        help="Number of days to add to the diagnose_date when pCT date is missing",
    )
    return argparser


def main() -> None:
    """Run the script."""
    argparser = create_parser()
    args = argparser.parse_args()

    dataset = pd.read_csv(args.input, header=[0, 1, 2])
    logger.info(f"Loaded {len(dataset)} patients from {args.input}")

    has_no_pct_date = (
        dataset["pCT", "core", "date"].isna() & ~dataset["pCT", "ipsi", "II"].isna()
    )
    # set the pCT date to one month after the diagnose_date
    dataset.loc[has_no_pct_date, ("pCT", "core", "date")] = (
        dataset.loc[has_no_pct_date, ("patient", "core", "diagnose_date")]
        .apply(lambda x: parse(x))
        .apply(lambda x: (x + timedelta(days=args.delta_days)).strftime("%Y-%m-%d"))
    )
    logger.info(f"Fixed {has_no_pct_date.sum()} patients with missing pCT date")

    lnls = dataset["pCT", "ipsi"].columns
    modalities = list(dataset.columns.levels[0])
    modalities.remove("patient")
    modalities.remove("tumor")
    has_no_info = dataset["patient", "core", "n_stage"] == 0
    for mod in modalities:
        has_no_info &= dataset[mod, "core", "date"].isna()

    dataset.loc[has_no_info, ("diagnostic_consensus", "core", "date")] = (
        dataset.loc[has_no_info, ("patient", "core", "diagnose_date")]
        .apply(lambda x: parse(x))
        .apply(lambda x: (x + timedelta(days=args.delta_days)).strftime("%Y-%m-%d"))
    )
    for side in ["ipsi", "contra"]:
        for lnl in lnls:
            dataset.loc[has_no_info, ("diagnostic_consensus", side, lnl)] = False
    logger.info(f"Added negative diagnostic consensus for {has_no_info.sum()} patients")

    dataset.to_csv(args.output, index=False)
    logger.success(f"Saved {len(dataset)} patients to {args.output}")


if __name__ == "__main__":
    main()
