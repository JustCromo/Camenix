"""Testi per l'utente, separati dal codice: un file JSON per lingua."""
import json
import os
from importlib import resources

_cache = {}


def _load(lang):
    if lang not in _cache:
        try:
            data = resources.files("camenix.i18n").joinpath(f"{lang}.json").read_text(encoding="utf-8")
            _cache[lang] = json.loads(data)
        except (FileNotFoundError, ValueError):
            _cache[lang] = {}
    return _cache[lang]


def lang():
    """Per ora solo italiano; le altre lingue arriveranno come nuovi file."""
    return os.environ.get("CAMENIX_LANG", "it")


def t(key, **kw):
    text = _load(lang()).get(key) or _load("it").get(key) or key
    try:
        return text.format(**kw)
    except (KeyError, IndexError, ValueError):
        return text
