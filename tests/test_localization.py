from pathlib import Path

import json

from game.localization import default_catalog, get_translator


def test_default_translator_returns_english_strings():
    translator = get_translator()
    assert translator.translate("ui.upgrade_prompt") == "Choose Upgrade [1-3]:"


def test_default_catalog_loads_languages_from_assets():
    catalog = default_catalog()
    languages = set(catalog.available_languages())
    assert {"en", "es"}.issubset(languages)
    english_entries = catalog.language_entries("en")
    assert english_entries["cli.description"].startswith("Nightfall Survivors")


def test_translator_uses_language_and_falls_back():
    translator = get_translator("es")
    assert translator.translate("ui.upgrade_prompt").startswith("Elige")
    assert translator.translate("nonexistent.key") == "nonexistent.key"


def test_catalog_registration_allows_new_languages():
    catalog = default_catalog()
    catalog.register_language("fr-test", {"ui.upgrade_prompt": "Choisissez une amélioration [1-3] :"}, inherit_from="en")
    translator = catalog.translator("fr-test", fallback="en")
    assert "Choisissez" in translator.translate("ui.upgrade_prompt")


def test_localization_files_are_well_formed():
    assets_dir = Path(__file__).resolve().parents[1] / "assets" / "loc"
    for json_path in assets_dir.glob("*.json"):
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        assert "strings" in payload and isinstance(payload["strings"], dict)
