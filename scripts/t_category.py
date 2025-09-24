# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "lyscripts @ git+https://github.com/lycosystem/lyscripts@b72d2fe74ba4ecccfdfa8b98724b4501ff1a9145",
#     "matplotlib==3.10.0",
#     "pandas==2.2.3",
#     "tueplots==0.0.17",
# ]
# [tool.uv]
# exclude-newer = "2025-07-30T00:00:00Z"
# ///

"""Plot the distribution over patient's T-category."""

import argparse
from pathlib import Path

import lydata  # noqa: F401
import matplotlib.pyplot as plt
import pandas as pd
from lyscripts.plots import COLORS
from shared import MPLSTYLE
from tueplots import figsizes, fontsizes


def create_label(percent):
    """Create label for pie chart."""
    if percent < 5:
        return ""

    return f"{percent:.0f}%"


OUTPUT_NAME = Path(__file__).with_suffix(".png").name


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the script."""
    parser = argparse.ArgumentParser(
        prog="age_and_sex",
        description=__doc__,
    )
    parser.add_argument(
        "data",
        type=Path,
        help="Path to the data file.",
    )
    return parser


def main() -> None:
    """Run the script."""
    parser = create_parser()
    args = parser.parse_args()

    data = pd.read_csv(args.data, header=[0, 1, 2])
    output_dir = args.data.parent / "figures"
    output_dir.mkdir(exist_ok=True)

    plt.style.use(MPLSTYLE)
    plt.rcParams.update(figsizes.icml2022_half())
    plt.rcParams.update(fontsizes.icml2022())
    fig, ax = plt.subplots()

    t_stage_labels = ["T1", "T2", "T3", "T4"]
    colors = [
        COLORS["green"],
        COLORS["blue"],
        COLORS["orange"],
        COLORS["red"],
    ]

    if 0 in data.ly.t_stage.values:
        t_stage_labels = ["T0", *t_stage_labels]
        colors = [COLORS["gray"], *colors]

    (
        data.groupby(("tumor", "core", "t_stage"))
        .size()
        .plot.pie(
            y=("tumor", "core", "t_stage"),
            ax=ax,
            colors=colors,
            labels=t_stage_labels,
            autopct=create_label,
            counterclock=False,
            startangle=90,
        )
    )

    plt.savefig(output_dir / OUTPUT_NAME, dpi=300)


if __name__ == "__main__":
    main()
