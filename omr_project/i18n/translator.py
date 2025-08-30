"""Runtime JSON-based translation loader.

Moves large inline dictionaries to external JSON files in `locales/`.
Provides fallback to English and logs missing keys for visibility.
"""

from __future__ import annotations

from pathlib import Path
import json
from typing import Dict, Any
from config.logger_config import get_logger, APP_LOGGER_NAME

_LOG = get_logger(APP_LOGGER_NAME)

LOCALES_DIR = Path(__file__).parent / "locales"
DEFAULT_LANG = "en"


class Translator:
    def __init__(self):
        self.current_language = DEFAULT_LANG
        self.translations: Dict[str, Dict[str, str]] = {}
        self._missing: set[str] = set()
        self._load_all_locales()

    def _load_all_locales(self):
        if not LOCALES_DIR.exists():  # pragma: no cover
            _LOG.warning("Locales directory missing: %s", LOCALES_DIR)
            return
        for file in LOCALES_DIR.glob("*.json"):
            try:
                with file.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    self.translations[file.stem] = {k: str(v) for k, v in data.items()}
                    _LOG.debug("Loaded locale '%s' with %d keys", file.stem, len(data))
            except Exception as e:  # pragma: no cover
                _LOG.error("Failed loading locale %s: %s", file.name, e)
        if DEFAULT_LANG not in self.translations:
            self.translations[DEFAULT_LANG] = {}

    def set_language(self, lang_code: str):
        if lang_code in self.translations:
            self.current_language = lang_code
        else:  # pragma: no cover
            _LOG.warning("Requested unknown language '%s'", lang_code)

    def t(self, key: str) -> str:
        lang_map = self.translations.get(self.current_language, {})
        if key in lang_map:
            return lang_map[key]
        # fallback to default
        default_map = self.translations.get(DEFAULT_LANG, {})
        if key in default_map:
            # log missing for current language only once
            missing_id = f"{self.current_language}:{key}"
            if missing_id not in self._missing:
                self._missing.add(missing_id)
                _LOG.debug("Missing key '%s' in language '%s' (using default)", key, self.current_language)
            return default_map[key]
        # total miss
        miss_token = f"[{key}]"
        if key not in self._missing:
            self._missing.add(key)
            _LOG.warning("Missing translation key '%s' in all languages", key)
        return miss_token


translator = Translator()
t = translator.t


def get_option_letter(index: int) -> str:
    if translator.current_language == 'el':
        greek_letters = ['Α', 'Β', 'Γ', 'Δ']
        return greek_letters[index] if index < len(greek_letters) else chr(65 + index)
    return chr(65 + index)
