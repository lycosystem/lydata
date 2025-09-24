# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "dateparser==1.2.2",
#     "icd10-cm==0.0.5",
#     "jinja2==3.1.6",
#     "lazydocs==0.4.8",
#     "lyscripts @ git+https://github.com/lycosystem/lyscripts@b72d2fe74ba4ecccfdfa8b98724b4501ff1a9145",
#     "pandas==2.2.3",
# ]
# [tool.uv]
# exclude-newer = "2025-07-30T00:00:00Z"
# ///

"""Render the `README.md` from the `README.md.jinja` and the docs for `mapping.py`."""

import argparse
import importlib.util
import sys
from pathlib import Path

import pandas as pd
from jinja2 import Environment, FileSystemLoader
from lazydocs import MarkdownGenerator
from lyscripts.data.lyproxify import generate_markdown_docs


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the script."""
    parser = argparse.ArgumentParser(
        prog="render",
        description=__doc__,
    )
    parser.add_argument(
        "-m",
        "--mapping",
        type=Path,
        default="mapping.py",
        help="Path to the mapping file.",
    )
    parser.add_argument(
        "-t",
        "--template",
        type=Path,
        default="README.md.jinja",
        help="Path to the template file.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default="README.md",
        help="Path to the output file.",
    )
    parser.add_argument(
        "-d",
        "--data",
        type=Path,
        default="data.csv",
        help="Path to the data file.",
    )
    return parser


def main() -> None:
    """Run the script."""
    parser = create_parser()
    args = parser.parse_args()

    # get number of patients from data file
    data = pd.read_csv(args.data, header=[0, 1, 2])
    num_patients = len(data)

    # dynamically load mapping module
    spec = importlib.util.spec_from_file_location("mapping", args.mapping)
    mapping = importlib.util.module_from_spec(spec)
    sys.modules["mapping"] = mapping
    spec.loader.exec_module(mapping)

    # get generator to generate markdown docs
    generator = MarkdownGenerator()

    # use jinja2 to render the template
    env = Environment(loader=FileSystemLoader(args.template.parent))  # noqa: S701
    template = env.get_template(args.template.name)
    result = template.render(
        num_patients=num_patients,
        column_description=generate_markdown_docs(mapping.COLUMN_MAP),
        mapping_docs=generator.import2md(mapping, depth=2),
    )

    # write result to output file
    with open(args.output, mode="w", encoding="utf-8") as f:
        f.write(result)


if __name__ == "__main__":
    main()
