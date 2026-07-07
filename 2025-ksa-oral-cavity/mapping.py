"""Map the `raw.csv` data from the 2025-ksa-oral-cavity cohort to the `data.csv` file.

This module defines how the command `lyscripts data lyproxify` (see
[the documentation](https://lyscripts.readthedocs.io/latest/) of the `lyscripts` module)
should handle the `raw.csv` data that was extracted at the Kantonsspital Aarau in order
to transform it into a [LyProX](https://lyprox.org)-compatible `data.csv` file.

The most important definitions in here are the list `EXCLUDE` and the dictionary
`COLUMN_MAP` that defines how to construct the new columns based on the `raw.csv` data.
They are described in more detail below:

---

### <kbd>global</kbd> `EXCLUDE`

List of tuples specifying which function to run for which columns to find out if
patients/rows should be excluded in the lyproxified `data.csv`.

The first element of each tuple is the flattened multi-index column name, the second
element is the function to run on the column to determine if a patient/row should be
excluded:

```python
EXCLUDE = [
    (column_name, check_function),
]
```

Essentially, a row is excluded, if for that row `check_function(raw_data[column_name])`
evaluates to `True`.

More information can be found in the
[documentation](https://lyscripts.readthedocs.io/latest/data/lyproxify.html#lyscripts.data.lyproxify.exclude_patients)
of the `lyproxify` function.

---

### <kbd>global</kbd> `COLUMN_MAP`

This is the actual mapping dictionary that describes how to transform the `raw.csv`
table into the `data.csv` table that can be fed into and understood by
[LyProX](https://lyprox.org).

See [the documentation](https://lyscripts.readthedocs.io/latest/data/lyproxify.html#lyscripts.data.lyproxify.transform_to_lyprox)
for details on how this dictionary is used by the `lyproxify` script.

It contains a tree-like structure that is human-readable and mimics the tree of
multi-level headers in the final `data.csv` file. For every column in the final
`data.csv` file, the dictionary describes from which columns in the `raw.csv` file the
data should be extracted and what function should be applied to it.

It also contains a `__doc__` key for every sub-dictionary that describes what the
respective column is about. This is used to generate the documentation for the
`README.md` file of this data.

---
"""

import re
import warnings
from collections.abc import Callable
from typing import Any

import pandas as pd
from dateutil.parser import parse

# columns that contain TNM info
TNM_COLS = [
    "cT stage",
    "cN stage",
    "pT stage",
    "pN stage",
]


def smpl_date(entry: str) -> str:
    """Parse date from string."""
    parsed_dt = parse(entry)
    return parsed_dt.strftime("%Y-%m-%d")


def robust(func: Callable) -> Any | None:
    """Return 'robust' type-conversion function.

    Do so by simply returning `None` whenever any exception is thrown.
    """

    def wrapper(entry, *_args, **_kwargs):
        if pd.isna(entry):
            return None
        try:
            return func(entry)
        except:  # noqa: E722
            warnings.warn(f"Failed to convert {entry=} using {func.__name__}.")
            return None

    return wrapper


def clean_cat(cat: str) -> int:
    """Extract T or N category as integer from the respective string.

    I.e., turn 'pN2+' into 2.
    """
    pattern = re.compile(r"[cp][TN]([0-4])[\s\S]*")
    match = pattern.match(str(cat))
    try:
        return int(match.group(1))
    except AttributeError:
        return None


def get_tnm_info(ct, cn, pt, pn) -> tuple[int, int, str]:
    """Determine the TNM edition used."""
    ct = clean_cat(ct)
    cn = clean_cat(cn)
    pt = clean_cat(pt)
    pn = clean_cat(pn)

    if pt is not None and pn is not None:
        return pt, pn, "p"

    if ct is not None and cn is not None:
        return ct, cn, "c"
    warnings.warn("No consistent TNM stage could be extracted.")
    if pt is not None and cn is not None:
        return pt, cn, "p"
    if ct is not None and pn is not None:
        return ct, pn, "c"
    raise ValueError("No TNM stage could be extracted.")


def get_t_category(*args, **_kwargs) -> int:
    """Extract the T-category."""
    (
        t_cat,
        _,
        _,
    ) = get_tnm_info(*args)
    return t_cat


def get_n_category(*args, **_kwargs) -> int:
    """Extract the N-category."""
    _, n_cat, _ = get_tnm_info(*args)
    return n_cat


def get_tnm_prefix(*args, **_kwargs) -> str:
    """Extract the TNM prefix."""
    _, _, prefix = get_tnm_info(*args)
    return prefix


def get_m_category(cat: str) -> int:
    """Extract M category as integer from the respective string.

    I.e., turn 'CM0' into 0. `-1` refers to `'X'`.
    """
    pattern = re.compile(r"cM([01x])")
    match = pattern.match(str(cat.strip()))
    try:
        return -1 if match.group(1) == "x" else int(match.group(1))
    except AttributeError:
        return None


def extract_hpv(
    value_hpv: int,
    value_p16: int | None,
    *_args,
    **_kwargs,
) -> bool | None:
    """Translate the HPV or p16 value (if HPV not available) to a boolean."""
    if value_hpv == 9:
        if value_p16 == 0:
            return False
        if value_p16 == 1:
            return True
        return None
    if value_hpv == 0:
        return False
    if value_hpv == 1:
        return True
    return None


def get_side(entry: str) -> str | None:
    """Extract on which side of the mid-sagittal plane the tumor is located."""
    if entry[0] == "R":
        return "right"
    if entry[0] == "L":
        return "left"
    if entry == "Midline":
        return "central"
    return None


EXCLUDE = [
    ("Inclusion (0: no, 1: yes)", lambda x: x == 0),
    ("cT stage", lambda x: x == "cTis"),
    ("pT stage", lambda x: x == "pTis"),
]

COLUMN_MAP = {
    "patient": {
        "__doc__": "This top-level header contains general patient information.",
        "core": {
            "__doc__": (
                "The second level header for the 'patient' columns is only a "
                "placeholder."
            ),
            "id": {
                "__doc__": "The patient ID.",
                "func": str,
                "columns": ["ID"],
            },
            "institution": {
                "__doc__": "Institution where the patient was treated",
                "default": "Kantonsspital Aarau",
            },
            "sex": {
                "__doc__": "The biological sex of the patients.",
                "func": lambda x1, x2, *a, **k: "male"
                if x1 == 1 and x2 == 0
                else "female"
                if x1 == 0 and x2 == 1
                else (
                    warnings.warn(f"Invalid gender encoding: {x1=}, {x2=}") or "invalid"
                ),
                "columns": [
                    "Gender (0: female, 1: male)",
                    "Gender (0: male, 1: female)",
                ],
            },
            "age": {
                "__doc__": "Age of the patient at the time of diagnosis",
                "func": robust(int),
                "columns": ["Age"],
            },
            "weight": {
                "__doc__": "The weight of the patient at the time of diagnosis.",
                "func": robust(float),
                "columns": ["Weight"],
            },
            "diagnose_date": {
                "__doc__": ("The date of diagnosis."),
                "func": robust(smpl_date),
                "columns": ["ED (date of diagnosis)"],
            },
            "alcohol_abuse": {
                "__doc__": (
                    "Whether the patient was abusingly drinking alcohol at the time of"
                    " diagnosis."
                ),
                "func": lambda x, *a, **k: False
                if x == 0
                else True
                if x == 1
                else None,
                "columns": ["Alcohol (0: no, 1: yes, 9: n/a)"],
            },
            "nicotine_abuse": {
                "__doc__": (
                    "Whether the patient was smoking nicotine at the time of diagnosis."
                ),
                "func": lambda x, *a, **k: False
                if x == 0
                else True
                if x == 1
                else None,
                "columns": ["Smoking (0: no, 1: yes, 9: n/a)"],
            },
            "hpv_status": {
                "__doc__": "The HPV p16 status of the patient.",
                "func": extract_hpv,
                "columns": [
                    "p16 (0: negative, 1: positive, 9: n/a)",
                    "HPV (0: negative, 1: positive, 9: n/a)",
                ],
            },
            "neck_dissection": {
                "__doc__": ("Whether the patient underwent a neck dissection."),
                "func": lambda x, *a, **k: False if x == 0 else True,
                "columns": ["Neck dissection (0: no, 1: yes)"],
            },
            "tnm_edition": {
                "__doc__": (
                    "The edition of the TNM classification used."
                    "This information is not available in this dataset."
                ),
                "default": None,
            },
            "n_stage": {
                "__doc__": "The N category of the patient.",
                "func": get_n_category,
                "columns": TNM_COLS,
            },
            "m_stage": {
                "__doc__": "The M category of the patient. `-1` refers to `'X'`.",
                "func": get_m_category,
                "columns": ["M stage"],
            },
            "extracapsular": {
                "__doc__": (
                    "Whether the patient had extracapsular spread. In this dataset, "
                    "this information is only globally available, not for each "
                    "individual lymph node level."
                ),
                "func": lambda x, *a, **k: False
                if x == 0
                else True
                if x == 1
                else None,
                "columns": ["Extracapsular extension (0: no, 1: yes, 9: n/a)"],
            },
        },
    },
    # Tumor information
    "tumor": {
        "__doc__": "This top-level header contains general tumor information.",
        "core": {
            "__doc__": "The second level header enumerates synchronous tumors.",
            "location": {
                "__doc__": (
                    # specific location or just 'oral cavity' ?
                    "The location of the tumor."
                ),
                "func": robust(str),
                "columns": ["Subside summary"],
            },
            "subsite": {
                "__doc__": "The subsite of the tumor, specified by ICD-O-3 code.",
                "func": lambda x, *_a, **_kw: x,
                "columns": ["ICD"],
            },
            "side": {
                "__doc__": (
                    "Whether the tumor occurred on the right or left side of the"
                    " mid-sagittal plane."
                ),
                "func": get_side,
                "columns": ["Primary tumor laterality"],
            },
            "central": {
                "__doc__": (
                    "Whether the tumor is located centrally w.r.t. the mid-sagittal "
                    "plane."
                ),
                "func": lambda x, *a, **k: True if x == "Midline" else False,
                "columns": ["Primary tumor laterality"],
            },
            "extension": {
                "__doc__": "Whether the tumor extended over the mid-sagittal line.",
                "func": lambda x, *a, **k: False
                if x == 0
                else True
                if x == 1
                else None,
                "columns": ["PT midline crossing (0: no, 1: yes, 9: n/a)"],
            },
            "distance_midline": {
                "__doc__": (
                    "The distance of the primary tumor to the mid-sagittal plane in mm."
                ),
                "func": robust(float),
                "columns": ["PT midline distance in mm"],
            },
            "volume": {
                "__doc__": "The volume of the tumor in cm^3.",
                "func": robust(float),
                "columns": ["PT volume"],
            },
            "t_stage_prefix": {
                "__doc__": "The prefix of the T category.",
                "func": get_tnm_prefix,
                "columns": TNM_COLS,
            },
            "t_stage": {
                "__doc__": "The T category of the tumor.",
                "func": get_t_category,
                "columns": TNM_COLS,
            },
        },
    },
    # Diagnostic consensus
    "diagnostic_consensus": {
        "__doc__": (
            "This top-level header contains information about the diagnostic consensus."
        ),
        "core": {
            "__doc__": "This second-level header contains general information.",
            "date": {
                "__doc__": (
                    "The date of the diagnostic consensus (same as neck"
                    " dissection date)."
                ),
                "func": robust(smpl_date),
                "columns": ["Neck dissection date"],
            },
        },
        "ipsi": {
            "__doc__": "This reports the diagnostic consensus of the ipsilateral LNLs.",
            "Ia": {
                "func": lambda x: True if x == 1 else False if x == 0 else None,
                "columns": ["LNL 1a ipsi (0: no, 1: yes)"],
            },
            "Ib": {
                "__doc__": (
                    "E.g., this column reports the diagnostic consensus of the"
                    " ipsilateral LNL Ib."
                ),
                "func": lambda x: True if x == 1 else False if x == 0 else None,
                "columns": ["LNL 1b ipsi (0: no, 1: yes)"],
            },
            "II": {
                "func": lambda x: True if x == 1 else False if x == 0 else None,
                "columns": ["LNL 2 ipsi (0: no, 1: yes)"],
            },
            "III": {
                "func": lambda x: True if x == 1 else False if x == 0 else None,
                "columns": ["LNL 3 ipsi (0: no, 1: yes)"],
            },
            "IV": {
                "func": lambda x: True if x == 1 else False if x == 0 else None,
                "columns": ["LNL 4 ipsi (0: no, 1: yes)"],
            },
            "V": {
                "func": lambda x: True if x == 1 else False if x == 0 else None,
                "columns": ["LNL 5 ipsi (0: no, 1: yes)"],
            },
            "VI": {
                "func": lambda x: True if x == 1 else False if x == 0 else None,
                "columns": ["LNL 6 ipsi (0: no, 1: yes)"],
            },
            "VII": {
                "func": lambda x: True if x == 1 else False if x == 0 else None,
                "columns": ["LNL 7 ipsi (0: no, 1: yes)"],
            },
        },
        "contra": {
            "__doc__": (
                "This reports the diagnostic consensus of the contralateral LNLs."
            ),
            "Ia": {
                "func": lambda x: True if x == 1 else False if x == 0 else None,
                "columns": ["LNL 1a contra (0: no, 1: yes)"],
            },
            "Ib": {
                "func": lambda x: True if x == 1 else False if x == 0 else None,
                "columns": ["LNL 1b contra (0: no, 1: yes)"],
            },
            "II": {
                "func": lambda x: True if x == 1 else False if x == 0 else None,
                "columns": ["LNL 2 contra (0: no, 1: yes)"],
            },
            "III": {
                "__doc__": (
                    "Under this column, we report the diagnostic consensus of the"
                    " contralateral LNL III."
                ),
                "func": lambda x: True if x == 1 else False if x == 0 else None,
                "columns": ["LNL 3 contra (0: no, 1: yes)"],
            },
            "IV": {
                "func": lambda x: True if x == 1 else False if x == 0 else None,
                "columns": ["LNL 4 contra (0: no, 1: yes)"],
            },
            "V": {
                "func": lambda x: True if x == 1 else False if x == 0 else None,
                "columns": ["LNL 5 contra (0: no, 1: yes)"],
            },
            "VI": {
                "func": lambda x: True if x == 1 else False if x == 0 else None,
                "columns": ["LNL 6 contra (0: no, 1: yes)"],
            },
            "VII": {
                "func": lambda x: True if x == 1 else False if x == 0 else None,
                "columns": ["LNL 7 contra (0: no, 1: yes)"],
            },
        },
    },
}
