# backend/utils/team_utils.py

from __future__ import annotations

import re
import unicodedata


CANONICAL_TEAMS = {
    "Paris SG",
    "Marseille",
    "Lyon",
    "Monaco",
    "Lille",
    "Nice",
    "Rennes",
    "Lens",
    "Reims",
    "Montpellier",
    "Strasbourg",
    "Nantes",
    "Le Havre",
    "Brest",
    "Toulouse",
    "Auxerre",
    "Angers",
    "St Etienne",
    "Metz",
    "Lorient",
    "Clermont",
    "Troyes",
    "Paris FC",
}


TEAM_NAME_MAP = {
    # --- Canonical / DB names ---
    "Paris SG": "Paris SG",
    "Marseille": "Marseille",
    "Lyon": "Lyon",
    "Monaco": "Monaco",
    "Lille": "Lille",
    "Nice": "Nice",
    "Rennes": "Rennes",
    "Lens": "Lens",
    "Reims": "Reims",
    "Montpellier": "Montpellier",
    "Strasbourg": "Strasbourg",
    "Nantes": "Nantes",
    "Le Havre": "Le Havre",
    "Brest": "Brest",
    "Toulouse": "Toulouse",
    "Auxerre": "Auxerre",
    "Angers": "Angers",
    "St Etienne": "St Etienne",
    "Metz": "Metz",
    "Lorient": "Lorient",
    "Clermont": "Clermont",
    "Troyes": "Troyes",
    "Paris FC": "Paris FC",

    # --- Common aliases ---
    "Paris Saint-Germain": "Paris SG",
    "Paris Saint Germain": "Paris SG",
    "Paris-SG": "Paris SG",
    "PSG": "Paris SG",

    "Olympique de Marseille": "Marseille",
    "Olympique Marseille": "Marseille",

    "Olympique Lyonnais": "Lyon",
    "Olympique Lyon": "Lyon",

    "AS Monaco": "Monaco",

    "Lille OSC": "Lille",
    "LOSC Lille": "Lille",

    "OGC Nice": "Nice",

    "Stade Rennais": "Rennes",
    "Stade Rennais FC": "Rennes",

    "RC Lens": "Lens",
    "Racing Club De Lens": "Lens",

    "Stade de Reims": "Reims",

    "Montpellier HSC": "Montpellier",

    "RC Strasbourg Alsace": "Strasbourg",
    "Strasbourg Alsace": "Strasbourg",

    "FC Nantes": "Nantes",

    "Le Havre AC": "Le Havre",

    "Stade Brestois 29": "Brest",
    "Stade Brest 29": "Brest",
    "Stade Brestois": "Brest",

    "Toulouse FC": "Toulouse",

    "AJ Auxerre": "Auxerre",

    "Angers SCO": "Angers",

    "AS Saint-Étienne": "St Etienne",
    "Saint-Étienne": "St Etienne",
    "AS Saint-Etienne": "St Etienne",
    "Saint-Etienne": "St Etienne",
    "AS Saint Etienne": "St Etienne",
    "Saint Etienne": "St Etienne",

    "FC Metz": "Metz",

    "FC Lorient": "Lorient",

    "Clermont Foot": "Clermont",
    "Clermont Foot 63": "Clermont",

    "ESTAC Troyes": "Troyes",
    "ES Troyes AC": "Troyes",
}


def _strip_accents(value: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(ch)
    )


def _clean_team_name(name: str) -> str:
    if not name:
        return ""

    value = str(name).strip()
    value = value.replace("’", "'").replace("`", "'")
    value = value.replace("–", "-").replace("—", "-")
    value = _strip_accents(value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


_NORMALIZED_LOOKUP = {}
for raw_name, canonical in TEAM_NAME_MAP.items():
    cleaned = _clean_team_name(raw_name)
    _NORMALIZED_LOOKUP[cleaned] = canonical
    _NORMALIZED_LOOKUP[cleaned.lower()] = canonical


def normalise_team(name: str | None) -> str | None:
    """
    Return canonical DB team name, or None if not recognized.
    """
    if not name:
        return None

    cleaned = _clean_team_name(name)

    if cleaned in _NORMALIZED_LOOKUP:
        return _NORMALIZED_LOOKUP[cleaned]

    lower_cleaned = cleaned.lower()
    if lower_cleaned in _NORMALIZED_LOOKUP:
        return _NORMALIZED_LOOKUP[lower_cleaned]

    return None


def canonical_team_or_self(name: str | None) -> str:
    """
    Return canonical DB name if known, otherwise return cleaned input string.
    """
    if not name:
        return ""
    cleaned = _clean_team_name(name)
    return normalise_team(cleaned) or cleaned


def is_known_team(name: str | None) -> bool:
    return normalise_team(name) is not None