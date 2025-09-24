# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "lyscripts @ git+https://github.com/lycosystem/lyscripts@b72d2fe74ba4ecccfdfa8b98724b4501ff1a9145",
#     "matplotlib==3.10.0",
#     "numpy==2.2.6",
#     "pandas==2.2.3",
#     "tueplots==0.0.17",
# ]
# [tool.uv]
# exclude-newer = "2025-07-30T00:00:00Z"
# ///

"""Plot distribution over patient's age, stratified by sex and smoking status."""

import argparse
from pathlib import Path

import lydata  # noqa: F401
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from lydata import C
from lyscripts.plots import COLORS
from shared import MPLSTYLE
from tueplots import figsizes, fontsizes

OUTPUT_NAME = Path(__file__).with_suffix(".png").name


def create_parser() -> argparse.ArgumentParser:
    """Create an argument parser for the script."""
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
    """Run main function to execute the script."""
    parser = create_parser()
    args = parser.parse_args()

    data = pd.read_csv(args.data, header=[0, 1, 2])
    output_dir = args.data.parent / "figures"
    output_dir.mkdir(exist_ok=True)

    male_ages = data.ly.query(C("sex") == "male").ly.age.values
    male_smoker_ages = data.ly.query(
        (C("sex") == "male") & (C("smoke") == True),
    ).ly.age.values
    male_percent = 100 * len(male_ages) / len(data)
    male_smoker_percent = 100 * len(male_smoker_ages) / len(data)

    female_ages = data.ly.query(C("sex") == "female").ly.age.values
    female_smoker_ages = data.ly.query(
        (C("sex") == "female") & (C("smoke") == True),
    ).ly.age.values
    female_percent = 100 * len(female_ages) / len(data)
    female_smoker_percent = 100 * len(female_smoker_ages) / len(data)

    bins = np.linspace(0, 100, 21)
    hist_kwargs = {
        "bins": bins,
        "orientation": "horizontal",
        "zorder": 4,
    }

    plt.style.use(MPLSTYLE)
    plt.rcParams.update(
        figsizes.icml2022_full(
            nrows=1,
            ncols=2,
            height_to_width_ratio=0.75,
        ),
    )
    plt.rcParams.update(fontsizes.icml2022())
    fig, ax = plt.subplots(1, 2, sharey=True)

    ax[0].hist(
        male_ages,
        label=f"male ({male_percent:.1f}%)",
        color=COLORS["blue"],
        histtype="stepfilled",
        **hist_kwargs,
    )
    ax[0].hist(
        male_smoker_ages,
        label=f"smokers ({male_smoker_percent:.1f}%)",
        color="black",
        histtype="step",
        hatch="////",
        **hist_kwargs,
    )

    male_xlim = ax[0].get_xlim()
    ax[0].set_xlim(male_xlim[::-1])
    ax[0].set_ylim([0, 100])
    ax[0].yaxis.tick_right()
    ax[0].set_yticks(np.linspace(10, 90, 5))
    ax[0].set_yticks(np.linspace(20, 100, 5), minor=True)
    ax[0].set_yticklabels(np.linspace(10, 90, 5, dtype=int))
    ax[0].tick_params(axis="y", pad=7)
    ax[0].legend(loc="lower left")

    ax[1].hist(
        female_ages,
        label=f"female ({female_percent:.1f}%)",
        color=COLORS["red"],
        histtype="stepfilled",
        **hist_kwargs,
    )
    ax[1].hist(
        female_smoker_ages,
        label=f"smokers ({female_smoker_percent:.1f}%)",
        color="black",
        histtype="step",
        hatch="////",
        **hist_kwargs,
    )

    ax[1].set_xlim(male_xlim)
    ax[1].legend(loc="lower right")

    fig.supxlabel("number of patients", fontweight="normal", fontsize="medium")

    plt.savefig(output_dir / OUTPUT_NAME, dpi=300)


if __name__ == "__main__":
    main()
