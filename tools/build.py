"""Build the app from tools/template.html + tools/wordlists/*.json + audio/.

    python3 tools/build.py

Writes:
  ideogram-drills.html                standalone app, all audio embedded (works offline, share as one file)
  index.html                          website version (GitHub Pages): loads MP3s from audio/ on demand
  wordpress/wordpress-block.html      paste into a WordPress Custom HTML block (loads MP3s from AUDIO_BASE)
  wordpress/ideogram-audio.zip        the MP3s to upload to AUDIO_BASE on the server
Fails if a word has no MP3 for one of its voices (run tools/make_audio.py first).
"""
import base64, json, os, re, sys, zipfile
from common import ROOT, TOOLS, load_wordlists, words_of, audio_path, slug

AUDIO_BASE = "/wp-content/uploads/ideogram-audio"   # where the MP3 folders live on the WordPress server
START, END = "<!-- ═══ Ideogram", "<!-- ═══ end #idg-app ═══ -->"


def safe_json(obj):
    """JSON that can't break out of a <script> tag (JSON.parse reads \\u003c etc. back as < > &)."""
    s = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    return s.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")

def main():
    langs = load_wordlists()
    if not langs:
        sys.exit("No word lists in tools/wordlists/")

    missing = [f"{v['id']}: {w}" for L in langs for v in L["voices"] for w in words_of(L)
               if not os.path.exists(audio_path(v["id"], w))]
    if missing:
        sys.exit(f"{len(missing)} audio files missing, e.g. {missing[:5]}\nRun:  python3 tools/make_audio.py")

    config = {"languages": [{"code": L["code"], "name": L["name"],
                             "voices": [{"id": v["id"], "label": v.get("label", v["id"])} for v in L["voices"]],
                             "categories": L["categories"], "ui": L.get("ui", {})} for L in langs]}
    config_tag = '<script type="application/json" id="idg-config">' + safe_json(config) + "</script>"

    audio = {}
    for L in langs:
        for v in L["voices"]:
            audio[v["id"]] = {w: base64.b64encode(open(audio_path(v["id"], w), "rb").read()).decode() for w in words_of(L)}
    audio_tag = '<script type="application/json" id="idg-audio">' + safe_json(audio) + "</script>"

    t = open(os.path.join(TOOLS, "template.html"), encoding="utf-8").read()
    # Interface translations: every key must exist in UI_EN in the template; report gaps (English is used for them)
    block = re.search(r"var UI_EN = \{(.*?)\n  \};", t, re.S)
    ui_keys = set(re.findall(r"(\w+): \"", block.group(1))) if block else set()
    for L in langs:
        ui = L.get("ui", {})
        if L["code"] == "en" or not ui_keys:
            continue
        unknown, missing = sorted(set(ui) - ui_keys), sorted(ui_keys - set(ui))
        if unknown:
            sys.exit(f"{L['_file']}: unknown \"ui\" keys {unknown} (see UI_EN in tools/template.html)")
        if missing:
            print(f"  note: {L['_file']} has no translation for {missing}; English is used")
    for marker in ("<!--CONFIG-->", "<!--AUDIO-->", '"__AUDIO_BASE__"', START, END):
        if marker not in t:
            sys.exit(f"template.html is missing the marker {marker}")

    page = t.replace("<!--CONFIG-->", config_tag).replace("<!--AUDIO-->", audio_tag)
    with open(os.path.join(ROOT, "ideogram-drills.html"), "w", encoding="utf-8") as f:
        f.write(page)

    # Website (GitHub Pages): same page, but MP3s are fetched from audio/ when needed, so it stays small
    web = t.replace("<!--CONFIG-->", config_tag).replace("<!--AUDIO-->", "").replace('"__AUDIO_BASE__"', json.dumps("audio"))
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(web)

    wp = t.replace("<!--CONFIG-->", config_tag).replace("<!--AUDIO-->", "").replace('"__AUDIO_BASE__"', json.dumps(AUDIO_BASE))
    os.makedirs(os.path.join(ROOT, "wordpress"), exist_ok=True)
    with open(os.path.join(ROOT, "wordpress", "wordpress-block.html"), "w", encoding="utf-8") as f:
        f.write(wp[wp.index(START):wp.index(END) + len(END)] + "\n")

    with zipfile.ZipFile(os.path.join(ROOT, "wordpress", "ideogram-audio.zip"), "w", zipfile.ZIP_STORED) as z:
        for L in langs:
            for v in L["voices"]:
                for w in words_of(L):
                    z.write(audio_path(v["id"], w), f"{v['id']}/{slug(w)}.mp3")

    n_words = sum(len(words_of(L)) for L in langs)
    n_files = sum(len(words_of(L)) * len(L["voices"]) for L in langs)
    print(f"Built: {len(langs)} language(s) [{', '.join(L['code'] for L in langs)}], {n_words} words, {n_files} audio files")
    print(f"  ideogram-drills.html  ({os.path.getsize(os.path.join(ROOT, 'ideogram-drills.html')) / 1e6:.1f} MB)")
    print(f"  index.html            ({os.path.getsize(os.path.join(ROOT, 'index.html')) / 1e3:.0f} KB, website: loads MP3s from audio/)")
    print("  wordpress/wordpress-block.html, wordpress/ideogram-audio.zip")


if __name__ == "__main__":
    main()
