"""Localization utilities for translating prototype strings."""

from __future__ import annotations

import json
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Iterable, Mapping


class SafeFormatDict(dict):
    """Dictionary that leaves unknown fields untouched during formatting."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


@dataclass(frozen=True)
class LocalizationCatalog:
    """Holds string tables for multiple languages."""

    _languages: Dict[str, Dict[str, str]]

    def __init__(self) -> None:  # type: ignore[override]
        object.__setattr__(self, "_languages", {})

    def register_language(
        self,
        code: str,
        entries: Mapping[str, str],
        *,
        inherit_from: str | None = None,
    ) -> None:
        """Register a language table, optionally inheriting from another."""

        if not code:
            raise ValueError("language code must be provided")
        if inherit_from:
            base = dict(self._languages.get(inherit_from, {}))
        else:
            base = {}
        base.update(entries)
        self._languages[code] = base

    def available_languages(self) -> Iterable[str]:
        return tuple(sorted(self._languages))

    def language_entries(self, code: str) -> Mapping[str, str]:
        """Return a copy of the catalog entries for the given language."""

        if code not in self._languages:
            raise KeyError(f"language '{code}' is not registered")
        return dict(self._languages[code])

    def translator(self, language: str, fallback: str | None = None) -> "Translator":
        if not self._languages:
            raise RuntimeError("no languages registered in catalog")
        primary = language if language in self._languages else fallback or next(iter(self._languages))
        resolved_fallback = fallback or next(iter(self._languages))
        return Translator(self, primary, resolved_fallback)

    def resolve(self, language: str, key: str) -> str | None:
        table = self._languages.get(language)
        if not table:
            return None
        return table.get(key)


class Translator:
    """Translates keys using a catalog with fallback semantics."""

    def __init__(self, catalog: LocalizationCatalog, language: str, fallback: str) -> None:
        self._catalog = catalog
        self._language = language
        self._fallback = fallback

    @property
    def language(self) -> str:
        return self._language

    def translate(self, key: str, **params) -> str:
        template = self._catalog.resolve(self._language, key)
        if template is None:
            template = self._catalog.resolve(self._fallback, key)
        if template is None:
            return key
        return template.format_map(SafeFormatDict(params))


def _load_localization_files(directory: Path) -> Iterable[tuple[str, Dict[str, str], str | None]]:
    for path in sorted(directory.glob("*.json")):
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            raise ValueError(f"localization file {path} must contain an object")
        code = payload.get("code") or path.stem
        if not isinstance(code, str) or not code:
            raise ValueError(f"language code missing or invalid in {path}")
        strings = payload.get("strings")
        if not isinstance(strings, dict):
            raise ValueError(f"strings for language {code} must be a mapping")
        inherit = payload.get("inherit")
        if inherit is not None and not isinstance(inherit, str):
            raise ValueError(f"inherit field for language {code} must be a string if provided")
        normalized_strings: Dict[str, str] = {}
        for key, value in strings.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError(f"entries for language {code} must map strings to strings")
            normalized_strings[key] = value
        yield code, normalized_strings, inherit


def _build_default_catalog() -> LocalizationCatalog:
    catalog = LocalizationCatalog()
    asset_dir = Path(__file__).resolve().parent.parent / "assets" / "loc"
    if not asset_dir.exists():
        raise FileNotFoundError(f"localization asset directory not found: {asset_dir}")
    for code, strings, inherit in _load_localization_files(asset_dir):
        catalog.register_language(code, strings, inherit_from=inherit)
    return catalog


_DEFAULT_CATALOG = _build_default_catalog()


def default_catalog() -> LocalizationCatalog:
    """Return the default project catalog."""

    return _DEFAULT_CATALOG


def get_translator(language: str = "en", fallback: str | None = None) -> Translator:
    """Fetch a translator for the requested language."""

    catalog = default_catalog()
    return catalog.translator(language, fallback=fallback)

