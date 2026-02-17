"""Tests for translation key validation."""

from __future__ import annotations

import json
import re
from pathlib import Path


def get_translation_keys_from_code() -> set[str]:
    """Extract all translation_key values from Python code."""
    keys = set()
    component_dir = Path("custom_components/jablotron_volta")

    for py_file in component_dir.glob("*.py"):
        content = py_file.read_text()
        matches = re.findall(r'translation_key="([^"]+)"', content)
        keys.update(matches)

    return keys


def get_translation_keys_from_json(lang: str) -> set[str]:
    """Extract all translation keys from JSON file."""
    json_path = Path(f"custom_components/jablotron_volta/translations/{lang}.json")

    with json_path.open() as f:
        data = json.load(f)

    keys = set()
    for domain in data.get("entity", {}).values():
        keys.update(domain.keys())

    return keys


def test_translation_files_exist():
    """Test that translation files exist."""
    en_path = Path("custom_components/jablotron_volta/translations/en.json")
    cs_path = Path("custom_components/jablotron_volta/translations/cs.json")

    assert en_path.exists(), "en.json translation file missing"
    assert cs_path.exists(), "cs.json translation file missing"


def test_translation_files_valid_json():
    """Test that translation files are valid JSON."""
    en_path = Path("custom_components/jablotron_volta/translations/en.json")
    cs_path = Path("custom_components/jablotron_volta/translations/cs.json")

    with en_path.open() as f:
        en_data = json.load(f)

    with cs_path.open() as f:
        cs_data = json.load(f)

    assert "entity" in en_data, "en.json missing 'entity' key"
    assert "entity" in cs_data, "cs.json missing 'entity' key"


def test_translation_keys_match_between_languages():
    """Test that en.json and cs.json have the same keys."""
    en_keys = get_translation_keys_from_json("en")
    cs_keys = get_translation_keys_from_json("cs")

    # Climate entities (ch1, ch2, dhw) are handled specially
    climate_keys = {"ch1", "ch2", "dhw"}

    missing_in_cs = en_keys - cs_keys - climate_keys
    missing_in_en = cs_keys - en_keys - climate_keys

    assert not missing_in_cs, f"Keys in en.json but missing in cs.json: {missing_in_cs}"
    assert not missing_in_en, f"Keys in cs.json but missing in en.json: {missing_in_en}"


def test_code_translation_keys_exist_in_json():
    """Test that all translation_key values from code exist in en.json."""
    code_keys = get_translation_keys_from_code()
    json_keys = get_translation_keys_from_json("en")

    missing = code_keys - json_keys

    assert not missing, f"translation_key in code but missing in en.json: {missing}"


def test_no_abbreviations_in_translation_keys():
    """Test that translation_key values don't use abbreviations."""
    code_keys = get_translation_keys_from_code()

    # Common abbreviations that Home Assistant expands
    forbidden_patterns = [
        ("_temp", "_temperature", "Use _temperature not _temp"),
        ("_pos", "_position", "Use _position not _pos"),
        ("_pct", "_percent", "Use _percent not _pct"),
    ]

    issues = []

    for key in code_keys:
        for abbrev, full, message in forbidden_patterns:
            if abbrev in key and full not in key:
                issues.append(f"{key}: {message}")

    assert not issues, "Found translation_key abbreviations:\n" + "\n".join(issues)


def test_translation_key_naming_convention():
    """Test that translation_key values follow naming conventions."""
    code_keys = get_translation_keys_from_code()

    issues = []

    for key in code_keys:
        # Should be lowercase with underscores
        if not re.match(r"^[a-z0-9_]+$", key):
            issues.append(f"{key}: Should be lowercase with underscores only")

        # Should not start or end with underscore
        if key.startswith("_") or key.endswith("_"):
            issues.append(f"{key}: Should not start or end with underscore")

        # Should not have double underscores
        if "__" in key:
            issues.append(f"{key}: Should not contain double underscores")

    assert not issues, "Translation key naming issues:\n" + "\n".join(issues)


def test_all_translations_have_name_property():
    """Test that all translation entries have a 'name' property."""
    en_path = Path("custom_components/jablotron_volta/translations/en.json")

    with en_path.open() as f:
        data = json.load(f)

    issues = []

    for domain_name, domain_data in data.get("entity", {}).items():
        for key, value in domain_data.items():
            if "name" not in value:
                issues.append(f"{domain_name}.{key}: Missing 'name' property")
            elif not value["name"]:
                issues.append(f"{domain_name}.{key}: Empty 'name' property")

    assert not issues, "Translation entries missing 'name':\n" + "\n".join(issues)


def test_translation_coverage():
    """Test that we have good translation coverage."""
    code_keys = get_translation_keys_from_code()
    json_keys = get_translation_keys_from_json("en")

    # Should have at least 70 entity translations
    assert len(json_keys) >= 70, (
        f"Expected at least 70 translations, got {len(json_keys)}"
    )

    # At least 90% of code keys should be in translations
    coverage = len(code_keys & json_keys) / len(code_keys) * 100
    assert coverage >= 90, f"Translation coverage is {coverage:.1f}%, expected >= 90%"
