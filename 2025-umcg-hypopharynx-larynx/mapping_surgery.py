"""Transform `raw_surgery.csv` to `data_surgery.csv`.

This module defines how the command `lyscripts data lyproxify` (see
[the documentation](https://lyscripts.readthedocs.io/) for the documentation of the
`lyscripts` module) should handle the `raw_surgery.csv` data that was extracted at the
UMCG in order to transform it into a [LyProX](https://lyprox.org)-compatible
`data_surgery.csv` file.

The most important definitions in here are the list `EXCLUDE` and the dictionary
`COLUMN_MAP` that defines how to construct the new columns based on the
`raw_surgery.csv` data. They are described in more detail below:

---

### <kbd>global</kbd> `EXCLUDE`

List of tuples specifying which function to run for which columns to find out if
patients/rows should be excluded in the lyproxified `data_surgery.csv`.

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

This is the actual mapping dictionary that describes how to transform the
`raw_surgery.csv` table into the `data_surgery.csv` table that can be fed
into and understood by [LyProX](https://lyprox.org).

See [the documentation](https://lyscripts.readthedocs.io/latest/data/lyproxify.html#lyscripts.data.lyproxify.transform_to_lyprox)
for details on how this dictionary is used by the `lyproxify` script.

It contains a tree-like structure that is human-readable and mimics the tree of
multi-level headers in the final `data_surgery.csv` file. For every column in the
final `data_surgery.csv` file, the dictionary describes from which columns in the
`raw_surgery.csv` file the data should be extracted and what function should be
applied to it.

It also contains a `__doc__` key for every sub-dictionary that describes what the
respective column is about. This is used to generate the documentation for the
`README.md` file of this data.

---
"""

import re
from typing import Callable

import pandas as pd
from dateparser import parse as dateparse


def robust_int(entry, *_args, **_kwargs) -> int | None:
    """Robustly convert a string to int, if possible."""
    try:
        return int(entry)
    except (ValueError, TypeError):
        return None


def get_age(entry, *_args, **_kwargs) -> int | None:
    """Robustly convert a float string to int, if possible."""
    try:
        return int(float(entry))
    except (ValueError, TypeError):
        return -1


def robust_bool(entry, *_args, **_kwargs) -> bool | None:
    """Robustly convert a string to bool, if possible."""
    if pd.isna(entry):
        return None

    try:
        return bool(int(entry))
    except ValueError:
        return None


def is_smaller_or_nan(entry, threshold, *_args, **_kwargs) -> bool:
    """Check if a value is smaller than a threshold or NaN."""
    if pd.isna(entry):
        return True

    try:
        return int(entry) < threshold
    except ValueError:
        return None


def robust_date(entry, *_args, **_kwargs) -> str | None:
    """Robustly convert a string to date, if possible."""
    if pd.isna(entry):
        return None
    try:
        return dateparse(entry).strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        return None


def t_stage_mapping(*entry, **_kwargs) -> str:
    """Map the T stage to the TNM edition 7."""
    clinical, pathological = entry

    if not pd.isna(pathological):
        match = re.match(r"T(\d)([a-c]|NOS)?", pathological)
        if match:
            return int(match.group(1))

    return robust_int(clinical)


def t_stage_prefix(*entry, **_kwargs) -> str:
    """Map the T stage prefix to the TNM edition 7."""
    _, pathological = entry

    if not pd.isna(pathological):
        match = re.match(r"T(\d)([a-c]|NOS)?", pathological)
        if match:
            return "p"

    return "c"


def n_stage_mapping(*entry, **_kwargs) -> str:
    """Map the N stage to the TNM edition 7."""
    clinical, pathological = entry
    mapping = {0: 0, 1: 1, 2: 2, 3: 2, 4: 2, 5: 3, 9: 0}

    if not pd.isna(pathological):
        match = re.match(r"N(\d)[a-c]?", pathological)
        if match:
            return int(match.group(1))

    try:
        return mapping[int(clinical)]
    except (ValueError, TypeError):
        return None


def m_stage_mapping(*entry, **_kwargs) -> str:
    """Map the M stage to the TNM edition 7."""
    clinical, pathological = entry

    if not pd.isna(pathological):
        match = re.match(r"M(\d)", pathological)
        if match:
            return int(match.group(1))

    mapping = {0: 0, 1: 1, 9: -1}
    try:
        return mapping[int(clinical)]
    except (ValueError, TypeError):
        return None


def had_neck_dissection(entry, *_args, **_kwargs) -> bool | None:
    """Check if a patient had a neck dissection."""
    if pd.isna(entry):
        return None

    return isinstance(robust_date(entry), str)


def subsite_mapping(entry, *_args, **_kwargs) -> str:
    """Map from the numerical value to an ICD code."""
    mapping = {
        16: "C13.0",
        17: "C12",
        18: "C13.2",
        19: "C32.1",
        20: "C32.0",
        21: "C32.2",
        221: "C32.0",
    }
    try:
        return mapping[int(entry)]
    except (ValueError, TypeError):
        return None


def location_mapping(entry, *_args, **_kwargs) -> str:
    """Map the numerical column value to a primary tumor location."""
    mapping = {
        16: "hypopharynx",
        17: "hypopharynx",
        18: "hypopharynx",
        19: "larynx",
        20: "larynx",
        21: "larynx",
        221: "larynx",
    }
    try:
        return mapping[int(entry)]
    except (ValueError, TypeError):
        return None


def get_earlier_date(*date_entries, **_kwargs) -> str:
    """Return the earliest date from a list of dates."""
    dates = []
    for date_entry in date_entries:
        if pd.isna(date_entry):
            continue
        try:
            dates.append(dateparse(date_entry).strftime("%Y-%m-%d"))
        except (ValueError, AttributeError):
            pass

    return min(dates)


def is_dead(entry, *_args, **_kwargs) -> bool | None:
    """Check if a patient is dead."""
    entry = robust_int(entry)

    if entry is not None:
        return entry in [3, 4, 5]

    return entry


def cause_of_death(entry, *_args, **_kwargs) -> str | None:
    """Return the cause of death."""
    entry = robust_int(entry)

    if entry == 3:
        return "other"
    if entry == 4:
        return "tumor"
    if entry == 5:
        return "complication"

    return None


def had_complication(entry, *_args, **_kwargs) -> bool | None:
    """Check if a patient had a complication."""
    entry = robust_int(entry)

    if entry is not None:
        return entry == 5

    return entry


def safe_recurrence_date(rec, date, *_args, **_kwargs) -> str | None:
    """Return the date of recurrence if the patient had a recurrence."""
    rec = robust_bool(rec)
    date = robust_date(date)

    if not rec and date is not None:
        raise ValueError("Date of recurrence is set, but no recurrence is reported.")

    if rec and date is None:
        raise ValueError("Recurrence is reported, but no date of recurrence is set.")

    return date


def create_id_counter(start: int, prefix: str) -> Callable[[], str]:
    """Create a func to generates IDs counting from `start` with the given `prefix`."""
    counter = start

    def id_counter() -> str:
        nonlocal counter
        res = f"{prefix}{counter:04d}"
        counter += 1
        return res

    return id_counter


# Find the documentation for the variable below in the module-level docstring.
EXCLUDE = []

# Find the documentation for the variable below in the module-level docstring.
COLUMN_MAP = {
    # Patient information
    "patient": {
        "__doc__": (
            "General information about the patient's condition can be found under this "
            "top-level header."
        ),
        "core": {
            "__doc__": "General information about the patient.",
            "id": {
                "__doc__": "A unique patient ID.",
                "func": create_id_counter(start=1, prefix="UMCGs"),
                "columns": [],
            },
            "institution": {
                "__doc__": "The clinic where the data was extracted.",
                "default": "University Medical Center Groningen",
            },
            "sex": {
                "__doc__": "The biological sex of the patient.",
                "func": lambda x, *a, **k: "male" if x == 1 else "female",
                "columns": ["SEX_c"],
            },
            "age": {
                "__doc__": ("The age of the patient at the time of diagnosis."),
                "func": get_age,
                "columns": ["age"],
            },
            "diagnose_date": {
                "__doc__": (
                    "Date of diagnosis (format `YYYY-mm-dd`). In case the date of "
                    "diagnosis was missing, this may also report the date of surgery "
                    "or the start of radiotherapy."
                ),
                "func": get_earlier_date,
                "columns": [
                    "RTSTART_c",
                    "RTEIND_c",
                    "hh_dt_pa",
                    "hh_dt_ophals",
                    "hh_dtop_pt",
                    "TERM_c",
                    "DATLR_c",
                    "DATRR_c",
                    "DATMET_c",
                ],
            },
            "alcohol_abuse": {
                "__doc__": (
                    "`True` for patients who stated that they consume alcohol"
                    " regularly, `false` otherwise."
                ),
                "func": robust_bool,
                "columns": ["hh_cur_alcohol_use"],
            },
            "nicotine_abuse": {
                "__doc__": "Patients which are current or former smokers.",
                "func": robust_bool,
                "columns": ["hh_roken"],
            },
            "pack_years": {
                "__doc__": ("Number of pack years of smoking history, if available."),
                "func": robust_int,
                "columns": ["hh_pack_years"],
            },
            "hpv_status": {
                "__doc__": ("The HPV p16 status of the patient."),
                "func": robust_bool,
                "columns": ["p16"],
            },
            "neck_dissection": {
                "__doc__": (
                    "Indicates whether the patient has received a neck dissection as "
                    "part of the treatment."
                ),
                "func": had_neck_dissection,
                "columns": ["hh_dtop_pt"],
            },
            "tnm_edition": {
                "__doc__": (
                    "The edition of the TNM classification used to classify the "
                    "patient. In this dataset, only version 7 is used."
                ),
                "default": 7,
            },
            "n_stage": {
                "__doc__": (
                    "The N category of the patient, indicating the degree of spread to"
                    " regional lymph nodes."
                ),
                "func": n_stage_mapping,
                "columns": ["NSTAD_DEF_v7_c", "np"],
            },
            "m_stage": {
                "__doc__": (
                    "The M category of the patient, encoding the presence of distant"
                    " metastases."
                ),
                "func": m_stage_mapping,
                "columns": ["MSTAD_DEF_v7_c", "mp"],
            },
        },
    },
    # Tumor information
    "tumor": {
        "__doc__": "Information about tumors is stored under this top-level header.",
        "core": {
            "__doc__": "General information about the tumor.",
            "location": {
                "__doc__": (
                    "Anatomic location of the tumor. Since this dataset contains only"
                    " oropharyngeal SCC patients, this is always `oropharynx`."
                ),
                "func": location_mapping,
                "columns": ["LOCTUM_c"],
            },
            "subsite": {
                "__doc__": "The subsite of the tumor, specified by ICD-O-3 code.",
                "func": subsite_mapping,
                "columns": ["LOCTUM_c"],
            },
            "central": {
                "__doc__": (
                    "`true` when the tumor is located centrally on the mid-sagittal"
                    " plane."
                ),
                "func": robust_bool,
                "columns": ["central"],
            },
            "extension": {
                "__doc__": "`true` when the tumor extends over the mid-sagittal plane.",
                "func": robust_bool,
                "columns": ["midline_ext"],
            },
            "volume": {
                "__doc__": (
                    "The volume of the tumor in cm^3. Not reported in this dataset."
                ),
                "default": None,
            },
            "t_stage_prefix": {
                "__doc__": (
                    "Prefix modifier of the T-category. Can be 'c' or 'p'. In this"
                    " dataset, only the clinically assessed T-category is available."
                ),
                "func": t_stage_prefix,
                "columns": ["TSTAD_DEF_v7_c", "tp"],
            },
            "t_stage": {
                "__doc__": "T-category of the tumor, according to TNM staging.",
                "func": t_stage_mapping,
                "columns": ["TSTAD_DEF_v7_c", "tp"],
            },
            "dist_to_midline": {
                "__doc__": (
                    "Distance of the tumor to the mid-sagittal plane in millimeters."
                ),
                "default": None,
            },
        },
    },
    "diagnostic_consensus": {
        "__doc__": (
            "This top-level header contains the per-side and per-level clinical "
            "consensus on lymph node involvement. It was assessed based on different "
            "diagnostic modalities like CT or MRI."
        ),
        "core": {
            "__doc__": (
                "The second level header contains general information on the diagnostic"
                " consensus."
            ),
            "date": {
                "__doc__": (
                    "The date of the diagnostic consensus (same as date of diagnosis)."
                ),
                "func": get_earlier_date,
                "columns": [
                    "RTSTART_c",
                    "RTEIND_c",
                    "hh_dt_pa",
                    "hh_dt_ophals",
                    "hh_dtop_pt",
                    "TERM_c",
                    "DATLR_c",
                    "DATRR_c",
                    "DATMET_c",
                ],
            },
        },
        "ipsi": {
            "__doc__": (
                "These columns report the involvement based on the diagnostic consensus"
                " for ipsilateral LNLs."
            ),
            "I": {
                "func": robust_bool,
                "columns": ["hh_il1"],
            },
            "II": {
                "__doc__": (
                    "For example, the clinical involvement of ipsilateral level II "
                    "lymph nodes."
                ),
                "func": robust_bool,
                "columns": ["hh_il2"],
            },
            "III": {
                "func": robust_bool,
                "columns": ["hh_il3"],
            },
            "IV": {
                "func": robust_bool,
                "columns": ["hh_il4"],
            },
            "V": {
                "func": robust_bool,
                "columns": ["hh_il5"],
            },
            "VI": {
                "func": robust_bool,
                "columns": ["hh_il6"],
            },
            "VII": {
                "func": robust_bool,
                "columns": ["hh_rp_rs_il"],
            },
            "VIII": {
                "func": robust_bool,
                "columns": ["hh_il8"],
            },
            "IX": {
                "func": robust_bool,
                "columns": ["hh_il9"],
            },
            "X": {
                "func": robust_bool,
                "columns": ["hh_il10"],
            },
        },
        "contra": {
            "__doc__": (
                "These columns report the involvement based on the diagnostic consensus"
                " for contralateral LNLs."
            ),
            "I": {
                "func": robust_bool,
                "columns": ["hh_cl1"],
            },
            "II": {
                "func": robust_bool,
                "columns": ["hh_cl2"],
            },
            "III": {
                "func": robust_bool,
                "columns": ["hh_cl3"],
            },
            "IV": {
                "__doc__": (
                    "E.g., the clinical involvement of contralateral level IV "
                    "lymph nodes."
                ),
                "func": robust_bool,
                "columns": ["hh_cl4"],
            },
            "V": {
                "func": robust_bool,
                "columns": ["hh_cl5"],
            },
            "VI": {
                "func": robust_bool,
                "columns": ["hh_cl6"],
            },
            "VII": {
                "func": robust_bool,
                "columns": ["hh_rp_rs_cl"],
            },
            "VIII": {
                "func": robust_bool,
                "columns": ["hh_cl8"],
            },
            "IX": {
                "func": robust_bool,
                "columns": ["hh_cl9"],
            },
            "X": {
                "func": robust_bool,
                "columns": ["hh_cl10"],
            },
        },
    },
    "pathology": {
        "__doc__": (
            "This top-level header contains information on the pathological assessment "
            "of lymph nodes after neck dissection in binary form."
        ),
        "core": {
            "__doc__": "Second level header contains general information on pathology.",
            "date": {
                "__doc__": "The date of the pathological assessment.",
                "func": robust_date,
                "columns": ["hh_dtop_pt"],
            },
        },
        "ipsi": {
            "__doc__": "Columns reporting pathological involvement for ipsi LNLs.",
            "I": {
                "__doc__": (
                    "For instance, the pathological involvement of ipsilateral level I."
                ),
                "func": robust_bool,
                "columns": ["IL_L1_path"],
            },
            "II": {
                "func": robust_bool,
                "columns": ["IL_L2_path"],
            },
            "III": {
                "func": robust_bool,
                "columns": ["IL_L3_path"],
            },
            "IV": {
                "func": robust_bool,
                "columns": ["IL_L4_path"],
            },
            "V": {
                "func": robust_bool,
                "columns": ["IL_L5_path"],
            },
            "VI": {
                "func": robust_bool,
                "columns": ["IL_L6_path"],
            },
        },
        "contra": {
            "__doc__": "Columns reporting pathological involvement for contra LNLs.",
            "I": {
                "func": robust_bool,
                "columns": ["CL_L1_path"],
            },
            "II": {
                "func": robust_bool,
                "columns": ["CL_L2_path"],
            },
            "III": {
                "func": robust_bool,
                "columns": ["CL_L3_path"],
            },
            "IV": {
                "func": robust_bool,
                "columns": ["CL_L4_path"],
            },
            "V": {
                "func": robust_bool,
                "columns": ["CL_L5_path"],
            },
            "VI": {
                "func": robust_bool,
                "columns": ["CL_L6_path"],
            },
        },
    },
    "positive_dissected": {
        "__doc__": {
            "The total number of lymph nodes found to be metastatic in the "
            "pathological assessment after neck dissection, reported per LNL level.",
        },
        "core": {
            "__doc__": (
                "The second level header contains general information on the "
                "total number of nodes found to be positive."
            ),
            "date": {
                "__doc__": "The date of the pathological assessment.",
                "func": robust_date,
                "columns": ["hh_dtop_pt"],
            },
        },
        "ipsi": {
            "__doc__": "Number of involved lymph nodes for ipsilateral LNLs.",
            "I": {
                "func": robust_int,
                "columns": ["IL_L1_path"],
            },
            "II": {
                "func": robust_int,
                "columns": ["IL_L2_path"],
            },
            "III": {
                "func": robust_int,
                "columns": ["IL_L3_path"],
            },
            "IV": {
                "func": robust_int,
                "columns": ["IL_L4_path"],
            },
            "V": {
                "func": robust_int,
                "columns": ["IL_L5_path"],
            },
            "VI": {
                "func": robust_int,
                "columns": ["IL_L6_path"],
            },
        },
        "contra": {
            "__doc__": "Number of involved lymph nodes for contralateral LNLs.",
            "I": {
                "func": robust_int,
                "columns": ["CL_L1_path"],
            },
            "II": {
                "func": robust_int,
                "columns": ["CL_L2_path"],
            },
            "III": {
                "func": robust_int,
                "columns": ["CL_L3_path"],
            },
            "IV": {
                "__doc__": (
                    "E.g., the number of involved contralateral level IV lymph nodes."
                ),
                "func": robust_int,
                "columns": ["CL_L4_path"],
            },
            "V": {
                "func": robust_int,
                "columns": ["CL_L5_path"],
            },
            "VI": {
                "func": robust_int,
                "columns": ["CL_L6_path"],
            },
        },
    },
    "extracapsular": {
        "__doc__": (
            "This top-level header contains information on the presence of "
            "extracapsular spread (ECS) found in any lymph nodes of an LNL."
        ),
        "core": {
            "__doc__": "The second level header contains general information on ECS.",
            "date": {
                "__doc__": "The date of the pathological assessment of ECE.",
                "func": robust_date,
                "columns": ["hh_dtop_pt"],
            },
        },
        "ipsi": {
            "__doc__": "These columns report the presence of ECS for ipsilateral LNLs.",
            "I": {
                "func": robust_bool,
                "columns": ["IL_L1_ENS"],
            },
            "II": {
                "func": robust_bool,
                "columns": ["IL_L2_ENS"],
            },
            "III": {
                "func": robust_bool,
                "columns": ["IL_L3_ENS"],
            },
            "IV": {
                "func": robust_bool,
                "columns": ["IL_L4_ENS"],
            },
            "V": {
                "__doc__": (
                    "If `True`, this indicates the presence of ECS in at least one of "
                    "the ipsilateral level V lymph nodes."
                ),
                "func": robust_bool,
                "columns": ["IL_L5_ENS"],
            },
            "VI": {
                "func": robust_bool,
                "columns": ["IL_L6_ENS"],
            },
        },
        "contra": {
            "__doc__": "These columns report the presence of ECS for contra LNLs.",
            "I": {
                "func": robust_bool,
                "columns": ["CL_L1_ENS"],
            },
            "II": {
                "func": robust_bool,
                "columns": ["CL_L2_ENS"],
            },
            "III": {
                "func": robust_bool,
                "columns": ["CL_L3_ENS"],
            },
            "IV": {
                "func": robust_bool,
                "columns": ["CL_L4_ENS"],
            },
            "V": {
                "func": robust_bool,
                "columns": ["CL_L5_ENS"],
            },
            "VI": {
                "func": robust_bool,
                "columns": ["CL_L6_ENS"],
            },
        },
    },
}
