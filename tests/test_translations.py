"""Tests for translation coverage and naming."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from custom_components.jablotron_volta.binary_sensor import BINARY_SENSOR_TYPES
from custom_components.jablotron_volta.button import BUTTON_TYPES
from custom_components.jablotron_volta.number import NUMBER_TYPES
from custom_components.jablotron_volta.select import SELECT_TYPES
from custom_components.jablotron_volta.sensor import SENSOR_TYPES
from custom_components.jablotron_volta.switch import SWITCH_TYPES

TRANSLATIONS_DIR = Path("custom_components/jablotron_volta/translations")
LANGUAGES = ("en", "cs")

# platform -> translation keys used by code
CODE_TRANSLATION_KEYS: dict[str, set[str]] = {
    "sensor": {d.translation_key for d in SENSOR_TYPES},
    "binary_sensor": {d.translation_key for d in BINARY_SENSOR_TYPES},
    "number": {d.translation_key for d in NUMBER_TYPES},
    "select": {d.translation_key for d in SELECT_TYPES},
    "switch": {d.translation_key for d in SWITCH_TYPES},
    "button": {d.translation_key for d in BUTTON_TYPES},
    "climate": {"ch1", "ch2"},
}


def _load(lang: str) -> dict[str, Any]:
    with (TRANSLATIONS_DIR / f"{lang}.json").open() as f:
        return json.load(f)


def _flatten(data: dict[str, Any], prefix: str = "") -> set[str]:
    keys: set[str] = set()
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            keys |= _flatten(value, path)
        else:
            keys.add(path)
    return keys


@pytest.mark.parametrize("lang", LANGUAGES)
def test_code_translation_keys_exist(lang: str) -> None:
    """Every translation_key used by an entity has a name in each language."""
    entity = _load(lang)["entity"]
    missing = [
        f"{platform}.{key}"
        for platform, keys in CODE_TRANSLATION_KEYS.items()
        for key in keys
        if not entity.get(platform, {}).get(key, {}).get("name")
    ]
    assert not missing, f"{lang}.json missing entity names: {missing}"


@pytest.mark.parametrize("lang", LANGUAGES)
def test_select_options_translated(lang: str) -> None:
    """Every select option has a state translation, so the UI never shows raw keys."""
    selects = _load(lang)["entity"]["select"]
    missing = [
        f"{d.translation_key}.{option}"
        for d in SELECT_TYPES
        for option in d.options_map.values()
        if option not in selects[d.translation_key].get("state", {})
    ]
    assert not missing, f"{lang}.json missing select states: {missing}"


def test_languages_have_same_keys() -> None:
    """en.json and cs.json define exactly the same keys."""
    en_keys = _flatten(_load("en"))
    cs_keys = _flatten(_load("cs"))
    assert en_keys - cs_keys == set(), "Missing in cs.json"
    assert cs_keys - en_keys == set(), "Missing in en.json"


def test_no_unused_entity_translations() -> None:
    """Entity translations without a matching entity are dead strings."""
    entity = _load("en")["entity"]
    unused = [
        f"{platform}.{key}"
        for platform, keys in entity.items()
        for key in keys
        if key not in CODE_TRANSLATION_KEYS.get(platform, set())
    ]
    assert not unused, f"Unused entity translations: {unused}"


def test_no_abbreviations_in_translation_keys() -> None:
    """HA expands abbreviations in entity IDs; translation keys must use full words."""
    forbidden = {"_temp": "_temperature", "_pos": "_position", "_pct": "_percent"}
    issues = [
        f"{key}: use {full} not {abbrev}"
        for keys in CODE_TRANSLATION_KEYS.values()
        for key in keys
        for abbrev, full in forbidden.items()
        if abbrev in key and full not in key
    ]
    assert not issues, "\n".join(issues)


def test_translation_key_naming_convention() -> None:
    """Translation keys are lowercase snake_case."""
    pattern = re.compile(r"^[a-z0-9]+(_[a-z0-9]+)*$")
    bad = [
        key
        for keys in CODE_TRANSLATION_KEYS.values()
        for key in keys
        if not pattern.match(key)
    ]
    assert not bad, f"Invalid translation keys: {bad}"
