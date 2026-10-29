# Ideogram Drills: Specification

Version described: **v0.6** (October 2026). This file is the reference for evolving the app. Update it whenever behaviour, formats or the build process change.

---

## 1. Purpose

A practice tool for Controlled Remote Viewing (CRV) students to train **ideogram** production. A word is spoken; the student sketches an ideogram for it on paper before the countdown ends; the time allowed shrinks as the session goes on, pushing the response to become spontaneous rather than deliberate.

Origin: a Python/Tkinter drill (`Ideogram drills v0.1`) that read 194 words with the macOS `say` command at gaps of 5, 4, 3, 2 seconds per 20-word block.

### Users and context
- CRV students practising alone, on a computer or phone, with pen and paper.
- Online at **https://pgarralda-personal.github.io/Ideogram-Practice-app/** (GitHub Pages, public).
- Embedded in a **WordPress** site; also usable as a standalone HTML file (offline).

### Design principles
1. **Audio first.** The word is heard, not read; the screen shows "•" by default so the student is not cued visually.
2. **Timing must be trustworthy.** The countdown starts only after the word has finished playing.
3. **Natural voice.** Pre-recorded audio; the browser's speech engine is only a backup.
4. **Zero dependencies.** One HTML block, no external scripts, fonts or servers (beyond the MP3 files on WordPress).
5. **Embed-safe.** Must not be affected by, or affect, the host WordPress theme.

---

## 2. Features (v0.6)

| Area | Behaviour |
|---|---|
| Session | Words shuffled each run from the selected categories; length 20 / 50 / 100 / all. |
| Pace | **Smooth** (linear from start to end time), **Steps** (minus X s every N words, never below a minimum), **Fixed**. Live preview of the schedule. |
| Word speed-up | "Speed up words as time shortens" (on by default, hidden in Fixed): recorded words play faster as the time per word drops, from 1× up to "Fastest word speed" (1.1–2×, default 1.5×) at the session's shortest time. Pitch is kept (time-stretch, see 3). The current speed shows next to the word counter. Browser voice: its rate is multiplied by the same factor. |
| Countdown | Ring + seconds; grey while the word is playing, coloured during the response time. Progress bar for the session. |
| Controls | Start / Pause / Resume, Next, Stop. Keyboard: Space (start/pause), → (next), Esc (stop). |
| Voice | Recorded voices of the current language: all at random (default), or one voice; or the browser voice. Volume. Optional 880 Hz beep 0.38 s before each word. Test voice button. |
| Browser voice (backup) | Ranked voice list (natural / neural / premium / enhanced first; novelty voices hidden), speed control. Used automatically if a recording fails. |
| Language | Picker shown only when the build contains more than one language. Categories, voices and browser voice follow the language. |
| Categories | Chips per category (from the word list); at least one must be on. |
| Display | "Show word on screen" option (off by default). Light / dark follows the device. |
| Review | After a session: numbered word list; tap to mark a word missed; score (% in time) and the time range used. |
| Persistence | Settings saved per device in `localStorage` (`idg-settings`). |
| Device care | Screen Wake Lock during a session; iOS audio unlock on the first tap; `navigator.audioSession.type = "playback"` so iPhones play with the silent switch on. |

### Not yet (see Roadmap)
UI text translation, on-screen sketch pad, practice history, reveal-word-after-response mode.

---

## 3. Architecture

```
tools/wordlists/<lang>.json  ──►  tools/make_audio.py  ──►  audio/<voice>/<slug>.mp3
            │                                                      │
            └──────────────►  tools/build.py  ◄────────────────────┘
                                   │   (+ tools/template.html)
                                   ▼
        ideogram-drills.html   wordpress/wordpress-block.html   wordpress/ideogram-audio.zip
```

- **`tools/template.html`**: the whole app (HTML + CSS + JS). **Edit the app here only.** It contains markers the build replaces:
  - `<!--CONFIG-->` → `<script type="application/json" id="idg-config">` with languages, voices and categories.
  - `<!--AUDIO-->` → `<script type="application/json" id="idg-audio">` with every MP3 base64-encoded (standalone build only; empty in the WordPress block).
  - `"__AUDIO_BASE__"` → the server folder with the MP3s (WordPress block only).
  - `<!-- ═══ Ideogram …` and `<!-- ═══ end #idg-app ═══ -->` delimit the WordPress block.
- **Generated files are never edited by hand**: `ideogram-drills.html`, `wordpress/*`. Rebuild instead.
- The JS is one IIFE in ES5 style (no build step, no modules) so it runs in any browser WordPress users have.

### Embedding rules (WordPress safety)
- Everything lives inside `<div id="idg-app">`; every CSS rule is prefixed with `#idg-app`; element ids start with `idg-`.
- The block resets the properties themes commonly override on buttons/inputs (margin, text-transform, letter-spacing, box-shadow, height).
- No global variables (IIFE). Keyboard shortcuts ignore keys typed in inputs/selects.
- Alternative if a theme still interferes: embed the GitHub Pages copy with an `<iframe src="https://pgarralda-personal.github.io/Ideogram-Practice-app/ideogram-drills.html">` (no MP3 upload needed, since that file embeds the audio).

### Repository and hosting
- Code: **https://github.com/pgarralda-personal/Ideogram-Practice-app** (public), branch `main`.
- **GitHub Pages** serves `main` from the repository root. `index.html` is a small redirect to `ideogram-drills.html`, so the site root opens the app. Every push to `main` redeploys in about 1–2 minutes.
- `.gitignore` leaves out `_to_delete/`, `tools/models/` (voice model), Python caches and release zips (`Ideogram-Drills-*.zip`, `versions/*.zip`). Generated files (`ideogram-drills.html`, `wordpress/*`) **are** committed, because Pages serves them.
- Commits use the GitHub private address `8528405+pgarralda-personal@users.noreply.github.com` (set in this repo's git config), never a personal email.
- Past releases: git history and tags (`v0.6` onwards). `versions/` keeps only the releases from before the repo existed (v0.2–v0.4).

### Audio playback chain
1. **Recorded** (default): MP3 → `AudioContext.decodeAudioData` → `AudioBufferSourceNode` (through a gain node for volume). Source: embedded base64 (`#idg-audio`) if present, otherwise `fetch(AUDIO_BASE/<voice>/<slug>.mp3)`. Decoded buffers are cached; the next word is prefetched.
   - Speed-up: `stretch(buffer, rate)` time-stretches the decoded word without changing pitch (WSOLA: 30 ms Hann windows at 50 % overlap, input read every `15 ms × rate`, each window shifted up to ±8 ms to the best normalised cross-correlation with the previous one). ~20 ms per word; results are cached per buffer and rate, and the next word is stretched during prefetch.
2. If the recording is missing or fails → **browser speech** (`speechSynthesis`) with the selected/ranked voice and `lang` of the current language.
3. Safety timers resolve playback if `onended`/`onend` never fires (recorded: duration + 0.8 s; speech: estimate from word length).

Web Audio is used (not `<audio>` elements) because it gives exact end-of-playback timing, shares one unlocked context with the beep, and avoids per-word autoplay prompts on mobile.

### Session state machine
`idle → running ⇄ paused → idle`. A `runId` counter invalidates pending timers/callbacks on every state change. While running, each word: beep (optional) → play word → response gap (countdown) → next word. Pausing during playback repeats the word on resume; pausing during the gap resumes the remaining time.

---

## 4. Data formats

### 4.1 Word list: `tools/wordlists/<code>.json`
One file per language. Files whose name starts with `_` are ignored (examples, drafts).

```json
{
  "code": "es",                     // language code; also used for the browser-voice fallback (es, en, fr…)
  "name": "Español",                // shown in the language picker
  "kokoro_lang": "es",              // Kokoro phonemizer language: en-us, en-gb, es, fr-fr, it, pt-br, hi, ja, cmn
  "speed": 0.95,                    // Kokoro speaking speed
  "voices": [{"id": "ef_dora", "label": "Dora (femenina)"}, {"id": "em_alex", "label": "Alex (masculina)"}],
  "pronounce": {"Butte": "Byoot"},  // optional: text actually spoken when the spelling misleads the voice
  "categories": {
    "Tierra": ["Montaña", "Valle", "Desierto"],
    "Agua": ["Río", "Océano", "Cascada"]
  }
}
```
Rules (checked by the tools):
- Each voice id belongs to **one** language only.
- No duplicate words within a language (after accent/case folding).
- Category names are shown to the user as written; category order is the display order.

### 4.2 Audio files
- Path: `audio/<voice id>/<slug>.mp3`.
- `slug`: remove accents (Unicode NFD), lower-case, runs of anything other than `a-z0-9` → `_`, trim `_`. Examples: `Tide pool` → `tide_pool`, `Montaña` → `montana`, `Río` → `rio`. Implemented twice and **must stay identical**: `slug()` in `tools/common.py` and in `tools/template.html`.
- Format: MP3, mono, 24 kHz, 40 kbps. Processing: silence trimmed at both ends (−45 dB threshold), loudness normalised to −18 LUFS (true peak −1.5 dB), 50 ms tail. Typical length 0.6–1.1 s, ~4–8 KB.

### 4.3 Settings (`localStorage["idg-settings"]`)
`lang, src ("all" | voice id | "browser"), voice (browser voice name), rate, vol, beep, len ("20"|"50"|"100"|"0"=all), mode ("smooth"|"steps"|"fixed"), g0 (start / fixed time), g1 (end time or minimum), dec (step size s), every (words per step), wfast (speed up words, bool), wmax (fastest word speed, 1.1–2), show, catsBy ({lang: [category names]})`.
Older keys are migrated on load (`src:"both"` → `"all"`, `cats` → `catsBy.en`). When adding settings, add a default in `DEFAULTS`; never rename a key without a migration.

### 4.4 Pace formulas (word index i from 0, session length n, times in s, result rounded to 0.1 and never below 0)
Allowed values: start time `g0` 0.5–30 s; end time / minimum `g1` 0–30 s (0 = the next word follows as soon as the previous one ends).

- Fixed: `g0`
- Smooth: `g0 + (g1 − g0) · i / (n − 1)`
- Steps: `max(min(g0, g1), g0 − floor(i / every) · dec)`
- Word speed (when `wfast`, not Fixed): with `hi` = time of the first word and `lo` = time of the last, `1 + (wmax − 1) · (hi − gap_i) / (hi − lo)`, rounded to 0.05; 1× when `hi ≤ lo`.

---

## 5. Audio pipeline: how-tos

### Setup (once, on a Mac)
```bash
brew install ffmpeg
pip3 install kokoro-onnx soundfile
python3 tools/make_audio.py --list-voices     # first run downloads the voice model (~350 MB) to tools/models/
```
Voices are the open-source **Kokoro** model (Apache 2.0, free for commercial use). Voice id prefix: `a` US English, `b` UK English, `e` Spanish, `f` French, `i` Italian, `p` Brazilian Portuguese, `h` Hindi, `j` Japanese, `z` Mandarin; second letter `f` female / `m` male.

### Add or change words
1. Edit `tools/wordlists/en.json`.
2. `python3 tools/make_audio.py` (generates only the missing files).
3. Listen to the new files in `audio/<voice>/`. If one sounds wrong, add a respelling under `pronounce` and run `python3 tools/make_audio.py --words "That word" --force`.
4. `python3 tools/build.py`.
5. Test (section 6) and release (section 7). Removed words: their old MP3s can stay; the build only packages listed words.

### Add a language
1. Copy `tools/wordlists/_example-es.json` to `tools/wordlists/<code>.json` (no leading `_`), translate the categories and words, pick voices (`--list-voices`).
2. `python3 tools/make_audio.py --lang <code>`, listen, fix with `pronounce`.
3. `python3 tools/build.py`: the language picker now appears.
4. The standalone file grows by ~0.8 MB per voice per 194 words; WordPress loads files on demand, so its size is unaffected.

### Change voice or speed
Edit `voices` / `speed`, then `python3 tools/make_audio.py --lang <code> --force` (regenerates that language), then build.

### Use a different TTS service (e.g. ElevenLabs) or a human recording
Anything works as long as the result lands in `audio/<voice id>/<slug>.mp3`. For human recordings: record each word, export as files named by slug, run them through the same ffmpeg filter (see `FILTER` in `make_audio.py`) so loudness and trimming match, and add a matching voice entry in the word list.

---

## 6. Test checklist

Automated (before every release): build succeeds; open `ideogram-drills.html` (served over http, e.g. `python3 -m http.server`), run a 20-word session in each pace mode with short times, including an end time of 0 s; the word counter shows the speed rising to "Fastest word speed"; review shows 20 words; no console errors.

Manual, on real devices:
- [ ] Mac: Safari and Chrome. Test voice, full session, Space / → / Esc, pause during a word and during the countdown.
- [ ] iPhone (Safari): first word audible after tapping Start; works with the silent switch on; screen stays awake.
- [ ] Android (Chrome): same.
- [ ] WordPress staging page: block renders with the theme; MP3s load (open `<AUDIO_BASE>/af_heart/mountain.mp3` directly); dark mode looks right.
- [ ] Each language: picker, categories, both voices, browser fallback (choose "Browser voice").
- [ ] Word speed-up: listen to a session ending at 0 s; the fastest words sound natural (same pitch, no choppiness) at the chosen maximum.
- [ ] GitHub Pages: after the push, the site root opens the app and the tab title shows the new version (hard-reload if needed).
- [ ] Settings survive a reload.

---

## 7. Release process

1. Bump the version in `tools/template.html` (two places: `<title>` and the block comment), in this spec (top line, section 2 title, History) and in the README.
2. `python3 tools/build.py`.
3. Run the test checklist.
4. Commit and push: `git add -A && git commit -m "vX.Y: …" && git push`. Tag the release: `git tag vX.Y && git push origin vX.Y`.
5. Check GitHub Pages shows the new version (title of `ideogram-drills.html`).
6. WordPress: replace the Custom HTML block content with `wordpress/wordpress-block.html`; re-upload the MP3 folders only if words or voices changed (`wordpress/ideogram-audio.zip`).
7. Optional, for sharing offline: zip the project (exclude `versions/`, `tools/models/`, `_to_delete/`) or attach the zip to a GitHub Release.

---

## 8. Roadmap / backlog (proposed, in rough priority order)

1. **Translate the interface text** per language (labels, buttons, messages): move strings to a table keyed by language in the word list or template.
2. **Reveal mode**: show the word after its response time, for self-checking.
3. **Practice history**: store session scores locally; show trend over time.
4. **On-screen sketch pad** (touch/stylus): capture each ideogram as a thumbnail next to its word in the review.
5. **Custom word lists** entered by the user in the page.
6. **WordPress plugin with a shortcode** (`[ideogram_drills]`) bundling the MP3s, instead of a pasted block + manual upload.
7. Session presets (beginner / intermediate / advanced pace).

## 9. Known limitations
- Browser speech quality varies by device; it is only a fallback.
- `localStorage` settings are per browser and device; nothing is synced.
- The standalone file embeds all audio, so it grows with each language/voice.
- Kokoro pronunciation is occasionally off for rare words (use `pronounce`).
- Word speed-up is a simple time-stretch: fine up to ~1.5×; towards 2× some words can sound slightly rough.
- The GitHub Pages site is public: anyone with the link can use the app.
- `ideogram-drills.html` (~2.3 MB) is committed on every release, so the repository grows by roughly that much per release that changes the app.

## 10. History
- **v0.1**: Python/Tkinter + macOS `say`, gaps 5/4/3/2 s per 20 words.
- **v0.1 HTML**: browser port with Web Speech API.
- **v0.2**: robust speech (iOS unlock, voice ranking, fallbacks), smooth pace, session length, categories, countdown ring, pause/next/stop, review, settings memory, wake lock, WordPress-safe scoped CSS.
- **v0.3**: pre-recorded Kokoro voices (Heart, Michael), Web Audio playback, WordPress build loading MP3s.
- **v0.4**: configurable pace (smooth / steps / fixed) with preview.
- **v0.5**: word lists as per-language JSON; `make_audio.py` and `build.py` pipeline; language picker; accent-safe file names; this spec.
- **v0.5.1**: end time / "Never shorter than" can go down to 0 s (was 0.5 s). Project moved to GitHub; published on GitHub Pages.
- **v0.6**: words speed up (pitch kept) as the time per word shrinks: "Speed up words as time shortens" and "Fastest word speed" settings.
