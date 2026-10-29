# Ideogram Drills

CRV ideogram practice: words are spoken in random order, with a countdown that shortens as the session goes on.

**Try it online:** https://pgarralda-personal.github.io/Ideogram-Practice-app/
Full specification, data formats and how-tos: **[SPEC.md](SPEC.md)**.

## What's here
| Path | What it is |
|---|---|
| `index.html` | GitHub Pages entry point; redirects to the app. |
| `ideogram-drills.html` | The app (v0.6). Self-contained with all audio; double-click to open; works offline; share as one file. |
| `voice-sample.mp3` | Short sample of the two English voices. |
| `wordpress/wordpress-block.html` | Paste into a WordPress **Custom HTML** block. |
| `wordpress/ideogram-audio.zip` | MP3s for WordPress: unzip and upload the voice folders to `/wp-content/uploads/ideogram-audio/` (file manager / FTP). |
| `audio/` | All recorded words: `audio/<voice>/<word>.mp3`. |
| `tools/wordlists/` | The words, one JSON file per language (`en.json`; `_example-es.json` is a template for a new language). |
| `tools/make_audio.py` | Generates missing audio with the free Kokoro voices. |
| `tools/build.py` | Builds the app, the WordPress block and the audio zip. |
| `tools/template.html` | App source: edit the app here, never the built files. |
| `versions/` | Previous releases. |

## Common tasks
```bash
# one-time setup (Mac)
brew install ffmpeg
pip3 install kokoro-onnx soundfile

# after editing words in tools/wordlists/*.json
python3 tools/make_audio.py      # creates only the missing MP3s (first run downloads the voice model, ~350 MB)
python3 tools/build.py           # rebuilds ideogram-drills.html + wordpress/

# new language: copy tools/wordlists/_example-es.json to es.json, fill it in, then the two commands above
```
