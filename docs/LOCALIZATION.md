# Localization Workflow

This project keeps all player-facing strings in JSON catalogs that live under
`assets/loc/`. Each file contains the translations for a single language and is
loaded automatically when the game starts. The Python catalog in
`game/localization.py` merges the data, applies inheritance, and exposes a
translator object to the rest of the code base.

## File layout

```
assets/
  loc/
    en.json
    es.json
    de.json
    fr.json
    <language-code>.json
```

The name of the file normally matches the language code (`en`, `es`, etc.). The
file body is a JSON object with the following keys:

Active catalogs:

- English (`en`)
- Spanish (`es`)
- German (`de`, inherits `en`)
- French (`fr`, inherits `en`)

| Field      | Required | Description |
| ---------- | -------- | ----------- |
| `code`     | No       | Language identifier. Defaults to the file name. |
| `inherit`  | No       | Optional parent language to use for fallback strings. |
| `strings`  | Yes      | Mapping of translation keys to formatted strings. |

Example `fr.json`:

```json
{
  "code": "fr",
  "inherit": "en",
  "strings": {
    "ui.upgrade_prompt": "Choisissez une amélioration [1-3] :",
    "ui.run_survived": "AUBE ATTEINTE"
  }
}
```

Only the strings present in a language file are overridden. Any missing entries
fall back to the `inherit` language (and ultimately English).

## Adding a new language

1. Copy `assets/loc/en.json` to a new file named `<code>.json` where `<code>` is
   the BCP 47 language tag for your translation (for example `pt-BR`).
2. Update the top-level fields:
   * Set `code` to the same value as the file name, if you need a different tag.
   * Set `inherit` to the language your translation should fall back to, usually
     `en`.
3. Translate each entry in the `strings` dictionary. Keep interpolation tokens
   such as `{name}` or `{count}` intact—they are filled in at runtime.
4. Remove any keys that should use the fallback translation.

## Quality assurance checklist

Before opening a pull request:

* Run the extractor to ensure every key in the source code is present in the
  English catalog and to surface missing translations:
  ```bash
  python tools/extract_strings.py
  ```
  Pass `--fail-unused` if you want the command to exit with an error when
  unused catalog entries are detected.
* Execute the localization test suite to verify the JSON files load correctly:
  ```bash
  pytest tests/test_localization.py
  ```
* Double-check JSON syntax, escaping, and placeholder usage. Tests cover
  structural issues, but reviewers will look for typos and wording consistency
  as well.

Following this process keeps translations synchronized with the code and makes
it easy for contributors to add new locales safely.
