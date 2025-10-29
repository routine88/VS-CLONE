from game.localization import default_catalog, get_translator


def test_default_translator_returns_english_strings():
    translator = get_translator()
    assert translator.translate("ui.upgrade_prompt") == "Choose Upgrade [1-3]:"


def test_translator_uses_language_and_falls_back():
    translator = get_translator("es")
    assert translator.translate("ui.upgrade_prompt").startswith("Elige")
    assert translator.translate("nonexistent.key") == "nonexistent.key"


def test_catalog_registration_allows_new_languages():
    catalog = default_catalog()
    catalog.register_language("fr-test", {"ui.upgrade_prompt": "Choisissez une amélioration [1-3] :"}, inherit_from="en")
    translator = catalog.translator("fr-test", fallback="en")
    assert "Choisissez" in translator.translate("ui.upgrade_prompt")
