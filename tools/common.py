"""Shared helpers for make_audio.py and build.py."""
import json, os, re, sys, unicodedata

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
WORDLISTS = os.path.join(TOOLS, "wordlists")
AUDIO = os.path.join(ROOT, "audio")


def slug(word):
    """File name for a word. Must match slug() in tools/template.html."""
    s = unicodedata.normalize("NFD", word)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")  # strip accents
    s = re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
    return s


def load_wordlists(only=None):
    """Read tools/wordlists/*.json (files starting with '_' are ignored). English first."""
    langs = []
    for f in sorted(os.listdir(WORDLISTS)):
        if not f.endswith(".json") or f.startswith("_"):
            continue
        with open(os.path.join(WORDLISTS, f), encoding="utf-8") as fh:
            d = json.load(fh)
        d["_file"] = f
        if only and d["code"] not in only:
            continue
        langs.append(d)
    langs.sort(key=lambda d: (d["code"] != "en", d["code"]))
    validate(langs)
    return langs


def words_of(lang):
    return [w for ws in lang["categories"].values() for w in ws]


def validate(langs):
    errors, owner = [], {}
    for L in langs:
        engine = L.get("engine", "kokoro")
        if engine not in ("kokoro", "piper"):
            errors.append(f"{L['_file']}: unknown engine '{engine}' (kokoro or piper)")
        for k in ("code", "name", "voices", "categories") + (("kokoro_lang",) if engine == "kokoro" else ()):
            if k not in L:
                errors.append(f"{L['_file']}: missing '{k}'")
        if errors:
            continue
        if not L["voices"]:
            errors.append(f"{L['_file']}: needs at least one voice")
        for v in L["voices"]:
            if not re.fullmatch(r"[a-z0-9_]+", v["id"]):
                errors.append(f"{L['_file']}: voice id {v['id']!r} may only use a-z, 0-9 and _ (it is a folder name)")
            if v["id"] in owner:
                errors.append(f"voice {v['id']} is used by both '{owner[v['id']]}' and '{L['code']}' (each voice belongs to one language)")
            owner[v["id"]] = L["code"]
        seen = {}
        for w in words_of(L):
            s = slug(w)
            if not s:
                errors.append(f"{L['_file']}: word {w!r} gives an empty file name")
            elif s in seen:
                errors.append(f"{L['_file']}: {w!r} and {seen[s]!r} share the file name {s}.mp3 (duplicate word?)")
            seen[s] = w
    if errors:
        sys.exit("Word list problems:\n  - " + "\n  - ".join(errors))


def audio_path(voice, word):
    return os.path.join(AUDIO, voice, slug(word) + ".mp3")
