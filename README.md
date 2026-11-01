# Ideogram Drills

CRV ideogram practice: words are spoken in random order, with a countdown that shortens as the session goes on.

**Try it online:** https://pgarralda-personal.github.io/Ideogram-Practice-app/
Full specification, data formats and how-tos: **[SPEC.md](SPEC.md)**.

## What's here
| Path | What it is |
|---|---|
| `index.html` | The app for the website (GitHub Pages): loads the MP3s from `audio/` as needed. |
| `ideogram-drills.html` | The app, offline version (v0.7). Self-contained with all audio; double-click to open; works offline; share as one file. |
| `vision-sin-ojos/index.html` | Redirect only. The "Visión sin ojos" app moved to its own repo: https://github.com/pgarralda-personal/Vision-sin-ojos (online at https://pgarralda-personal.github.io/Vision-sin-ojos/). |
| `voice-sample.mp3` | Short sample of the two English voices. |
| `wordpress/wordpress-block.html` | Paste into a WordPress **Custom HTML** block. |
| `wordpress/ideogram-audio.zip` | MP3s for WordPress: unzip and upload the voice folders to `/wp-content/uploads/ideogram-audio/` (file manager / FTP). |
| `audio/` | All recorded words: `audio/<voice>/<word>.mp3`. |
| `tools/wordlists/` | Words and interface text, one JSON file per language: `en`, `de`, `es`, `fr`, `it`, `pt` (`_example-es.json` is a template). |
| `tools/make_audio.py` | Generates missing audio with free voices (Kokoro; Piper for German). |
| `tools/build.py` | Builds the website app, the offline app, the WordPress block and the audio zip. |
| `tools/template.html` | App source: edit the app here, never the built files. |
| `versions/` | Releases from before the GitHub repo (v0.2–v0.4); newer ones are in git history and tags. |

## Common tasks
```bash
# one-time setup (Mac)
brew install ffmpeg
brew install python@3.12 && python3.12 -m venv tools/.venv && tools/.venv/bin/pip install -r tools/requirements.txt

# after editing words in tools/wordlists/*.json
tools/.venv/bin/python tools/make_audio.py   # creates only the missing MP3s (first run downloads the voice models)
python3 tools/build.py           # rebuilds index.html, ideogram-drills.html and wordpress/

# new language: copy tools/wordlists/_example-es.json to <code>.json, fill in words, voices and "ui" texts, then the two commands above
```
