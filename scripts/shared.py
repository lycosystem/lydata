"""Shared variables and functions for the scripts."""

from pathlib import Path

LNLS = ["I", "II", "III", "IV", "V"]
MPLSTYLE = Path(__file__).parent / ".mplstyle"
COLORS = {
    "blue": "#005ea8",
    "orange": "#f17900",
    "green": "#00afa5",
    "red": "#ae0060",
    "gray": "#c5d5db",
}
SUBSITES: dict[str, tuple[str, str]] = {
    "C00.4": ("oral cavity", "Lower lip, inner aspect"),  # one ISB patient has this
    "C01": ("oropharynx", "Base of Tongue"),
    "C01.9": ("oropharynx", "Base of Tongue"),
    "C02": ("oral cavity", "Tongue"),
    "C02.0": ("oral cavity", "Dorsal surface of tongue"),
    "C02.1": ("oral cavity", "Border of tongue"),
    "C02.2": ("oral cavity", "Ventral surface of tongue"),
    "C02.3": ("oral cavity", "Anterior two-thirds of tongue"),
    "C02.4": ("oral cavity", "Lingual tonsil"),
    "C02.8": ("oral cavity", "Overlapping lesion of tongue"),
    "C02.9": ("oral cavity", "Tongue, unspecified"),
    "C03": ("oral cavity", "Gum"),
    "C03.0": ("oral cavity", "Upper gum"),
    "C03.1": ("oral cavity", "Lower gum"),
    "C03.9": ("oral cavity", "Gum, unspecified"),
    "C04": ("oral cavity", "Floor of Mouth"),
    "C04.0": ("oral cavity", "Anterior floor of mouth"),
    "C04.1": ("oral cavity", "Lateral floor of mouth"),
    "C04.8": ("oral cavity", "Overlapping lesion of floor of mouth"),
    "C04.9": ("oral cavity", "Floor of mouth, unspecified"),
    "C05": ("oral cavity", "Palate"),
    "C05.0": ("oral cavity", "Hard palate"),
    "C05.1": ("oral cavity", "Soft palate"),
    "C05.2": ("oral cavity", "Uvula"),
    "C05.8": ("oral cavity", "Overlapping lesion of palate"),
    "C05.9": ("oral cavity", "Palate, unspecified"),
    "C06": ("oral cavity", "Other and unspecified parts of mouth"),
    "C06.0": ("oral cavity", "Cheek mucosa"),
    "C06.1": ("oral cavity", "Vestibule of mouth"),
    "C06.2": ("oral cavity", "Retromolar area"),
    "C06.8": (
        "oral cavity",
        "Overlapping lesion of other and unspecified parts of mouth",
    ),  # noqa: E501
    "C06.9": ("oral cavity", "Mouth, unspecified"),
    #     "C08": "Salivary glands",
    #     "C08.0": "Submandibular gland",
    #     "C08.1": "Sublingual gland",
    #     "C08.9": "Major salivary gland, unspecified",
    "C09": ("oropharynx", "Tonsil"),
    "C09.0": ("oropharynx", "Tonsillar fossa"),
    "C09.1": ("oropharynx", "Tonsillar pillar (anterior)(posterior)"),
    "C09.8": ("oropharynx", "Overlapping lesion of tonsil"),
    "C09.9": ("oropharynx", "Tonsil, unspecified"),
    "C10": ("oropharynx", "Oropharynx"),
    "C10.0": ("oropharynx", "Vallecula"),
    "C10.1": ("oropharynx", "Anterior surface of epiglottis"),
    "C10.2": ("oropharynx", "Lateral wall of oropharynx"),
    "C10.3": ("oropharynx", "Posterior wall of oropharynx"),
    "C10.4": ("oropharynx", "Branchial cleft"),
    "C10.8": ("oropharynx", "Overlapping lesion of oropharynx"),
    "C10.9": ("oropharynx", "Oropharynx, unspecified"),
    "C12": ("hypopharynx", "Piriform sinus"),
    "C12.9": ("hypopharynx", "Piriform sinus"),
    "C13": ("hypopharynx", "Hypopharynx"),
    "C13.0": ("hypopharynx", "Postcricoid region"),
    "C13.1": ("hypopharynx", "Aryepiglottic fold, hypopharyngeal aspect"),
    "C13.2": ("hypopharynx", "Posterior wall of hypopharynx"),
    "C13.8": ("hypopharynx", "Overlapping lesion of hypopharynx"),
    "C13.9": ("hypopharynx", "Hypopharynx, unspecified"),
    "C32": ("larynx", "Larynx"),
    "C32.0": ("larynx", "Glottis"),
    "C32.1": ("larynx", "Supraglottis"),
    "C32.2": ("larynx", "Subglottis"),
    "C32.3": ("larynx", "Laryngeal cartilage"),
    "C32.8": ("larynx", "Overlapping lesion of larynx"),
    "C32.9": ("larynx", "Larynx, unspecified"),
}


def icd_to_location(icd_code: str) -> str:
    """Convert an ICD code to a primary tumor location."""
    if icd_code in SUBSITES:
        return SUBSITES[icd_code][0]
    return "unknown"


def remove_artists(ax):
    """Remove all artists from the axes."""
    for artist in ax.lines + ax.patches + ax.collections:
        artist.remove()
