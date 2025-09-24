# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "lydata @ git+https://github.com/lycosystem/lydata-package@0c82338ecd2d1802b4d7db5685694bd8ff660298",
#     "matplotlib==3.10.6",
#     "pandas==2.3.2",
#     "typer==0.17.3",
#     "joblib==1.5.2",
#     "loguru==0.7.3",
#     "pyyaml==6.0.2",
#     "tueplots==0.2.1",
# ]
# ///
"""Script for plotting the number of patients against their diagnosis times.

Ideally, we would also want to display the number of published records over time, but
I'm afraid the plot would get messy and complicated.
"""

import re
import sys
from pathlib import Path

import lydata
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import typer
import yaml
from joblib import Memory
from loguru import logger
from shared import COLORS
from tueplots.figsizes import beamer_169
from tueplots.fontsizes import beamer

memory = Memory(".cache", verbose=0)
app = typer.Typer()


@memory.cache
def cached_fetch_data(ref: str = "dev") -> pd.DataFrame:
    """Fetch data with caching."""
    raw = pd.DataFrame()
    logger.info(f"Fetching data from lydata.private at {ref=}.")

    for dset in lydata.load_datasets(repo_name="lycosystem/lydata.private", ref=ref):
        raw = pd.concat([raw, dset], ignore_index=True)
        logger.debug(f"Loaded dataset {dset.attrs} with {len(dset)} rows.")

    return raw


@app.command()
def collection(
    output_file: Path = Path("timeline.png"),
    ref: str = "78b2b2fb1a4a719a927b4db16704aed24ad1fa3b",
) -> None:
    """Plot a timeline of patient diagnoses."""
    raw = cached_fetch_data(ref=ref)
    data = raw.copy()
    data["patient", "_extra", "counter"] = 1
    data = data.set_index(
        keys=[("patient", "core", "institution"), ("patient", "core", "id")],
    )
    data.index.names = ["institution", "id"]

    indicators = data.patient._extra.counter.astype("Int64").unstack(level=0).fillna(0)
    times = raw.set_index(
        ("patient", "core", "id"),
    ).patient.core.diagnose_date.sort_values()
    indicators, times = indicators.align(
        times,
        axis="index",
        join="right",
    )

    plt.stackplot(
        times,
        [indicators[col].cumsum() for col in indicators.columns],
        labels=indicators.columns,
    )
    plt.legend()
    plt.savefig(output_file)
    logger.success(f"Saved timeline plot to {output_file}.")


@app.command()
def publication(root_dir: Path = ".", today: str = "2025-09-08") -> None:
    """Plot a timeline of the number of published patient records."""
    dates, num = ["2021-10-01"], [0]

    for directory in Path(root_dir).iterdir():
        if not directory.is_dir() or not re.match(r"^\d{4}-\w+-.*", directory.name):
            logger.debug(f"Skipping {directory}.")
            continue

        logger.info(f"Processing {directory}...")

        cff_file = directory / "CITATION.cff"
        if cff_file.exists():
            logger.debug(f"Found {cff_file}.")
            cff = yaml.safe_load(cff_file.read_text())
            date = cff["date-released"]
            dates.append(date)

        data_file = directory / "data.csv"
        if data_file.exists():
            logger.debug(f"Found {data_file}.")
            df = pd.read_csv(data_file, header=[0, 1, 2])
            num.append(len(df))

    dates.append(pd.to_datetime(today))
    num.append(0)

    dates.append(pd.to_datetime("2026-01-01"))
    num.append(0)

    table = pd.DataFrame({"date": pd.to_datetime(dates), "num": num})
    table = table.sort_values("date").reset_index(drop=True)
    table["cumulative"] = table["num"].cumsum()

    past = table["date"] <= pd.to_datetime(today)
    future = table["date"] >= pd.to_datetime(today)

    plt.rcParams.update(beamer_169())
    plt.rcParams.update(beamer())
    plt.rcParams.update({"font.sans-serif": ["Arial", "DejaVu Sans"]})

    _fig, ax = plt.subplots(layout="constrained")

    ax.step(
        x=table.loc[past, "date"],
        y=table.loc[past, "cumulative"],
        where="post",
        color=COLORS["blue"],
        zorder=10,
    )
    ax.fill_between(
        x=table.loc[past, "date"],
        y1=table.loc[past, "cumulative"],
        step="post",
        color=COLORS["blue"],
        alpha=0.5,
        zorder=9,
        linewidth=0,
    )

    ax.step(
        x=table.loc[future, "date"],
        y=table.loc[future, "cumulative"],
        where="post",
        color=COLORS["orange"],
        zorder=10,
    )
    ax.fill_between(
        x=table.loc[future, "date"],
        y1=table.loc[future, "cumulative"],
        step="post",
        color=COLORS["orange"],
        alpha=0.5,
        zorder=9,
        linewidth=0,
    )

    ax.set_xlim(left=table["date"].min(), right=table["date"].max())
    ax.set_ylim(bottom=0, top=3000)
    ax.grid(visible=True, which="major", axis="y", color=COLORS["gray"])
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_minor_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    output_path = "publication_timeline.png"
    plt.savefig(output_path, bbox_inches="tight", dpi=300)

    logger.success(f"Saved publication timeline plot to {output_path}.")


if __name__ == "__main__":
    logger.remove()
    logger.add(sys.stdout, level="DEBUG")
    app()
