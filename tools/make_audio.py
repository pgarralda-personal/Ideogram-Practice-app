"""Generate the spoken word files with free, open-source voices.

    python3 tools/make_audio.py                 # every language, only words that have no MP3 yet
    python3 tools/make_audio.py --lang es       # one language
    python3 tools/make_audio.py --force         # redo everything (e.g. after changing speed)
    python3 tools/make_audio.py --words "Tide pool,Butte" --force   # redo some words
    python3 tools/make_audio.py --list-voices   # show the Kokoro voice ids

Engines (set per language with "engine" in the word list):
  kokoro  (default) Kokoro voices: en, es, fr, it, pt-br, hi, ja, zh. Model (~350 MB) downloaded to tools/models/ once.
  piper   Piper voices (e.g. German). Each voice's "model" (like de_DE-thorsten-high) is downloaded to
          tools/models/piper/ once. Voice list: https://huggingface.co/rhasspy/piper-voices

Needs:  pip install -r tools/requirements.txt     and ffmpeg on the PATH (macOS: brew install ffmpeg).
Output: audio/<voice>/<word>.mp3 — trimmed, loudness-normalised, mono 24 kHz, 40 kbps.
"""
import argparse, os, shutil, subprocess, sys, tempfile, urllib.request, wave
from common import TOOLS, load_wordlists, words_of, audio_path

MODELS = os.path.join(TOOLS, "models")
MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
MODEL_FILES = ["kokoro-v1.0.onnx", "voices-v1.0.bin"]
PIPER_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/"

# Audio processing: trim silence at both ends, normalise loudness to -18 LUFS, add 50 ms tail.
FILTER = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.03,areverse,"
          "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08,areverse,"
          "loudnorm=I=-18:TP=-1.5:LRA=7,apad=pad_dur=0.05")


def ensure_models():
    os.makedirs(MODELS, exist_ok=True)
    for f in MODEL_FILES:
        p = os.path.join(MODELS, f)
        if not os.path.exists(p):
            print(f"Downloading {f} (one time) ...", flush=True)
            urllib.request.urlretrieve(MODEL_URL + f, p + ".part")
            os.replace(p + ".part", p)
    return [os.path.join(MODELS, f) for f in MODEL_FILES]


def download(url, path):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        print(f"Downloading {os.path.basename(path)} (one time) ...", flush=True)
        urllib.request.urlretrieve(url, path + ".part")
        os.replace(path + ".part", path)
    return path


def piper_model(name):
    """de_DE-thorsten-high -> local .onnx path (downloads model + config the first time)."""
    loc, voice, quality = name.split("-")
    rel = f"{loc.split('_')[0]}/{loc}/{voice}/{quality}/{name}"
    base = os.path.join(MODELS, "piper", name)
    download(PIPER_URL + rel + ".onnx.json", base + ".onnx.json")
    return download(PIPER_URL + rel + ".onnx", base + ".onnx")


class Engines:
    """Loads each TTS engine / voice only when a language needs it."""
    def __init__(self):
        self._kokoro, self._piper = None, {}

    def kokoro(self):
        if self._kokoro is None:
            try:
                from kokoro_onnx import Kokoro
            except ImportError:
                sys.exit("Missing packages. Run:  pip install -r tools/requirements.txt")
            self._kokoro = Kokoro(*ensure_models())
        return self._kokoro

    def piper(self, model):
        if model not in self._piper:
            try:
                from piper import PiperVoice
            except ImportError:
                sys.exit("Missing packages. Run:  pip install -r tools/requirements.txt")
            self._piper[model] = PiperVoice.load(piper_model(model))
        return self._piper[model]

    def check(self, L, v):
        if L.get("engine", "kokoro") == "kokoro" and v["id"] not in self.kokoro().get_voices():
            sys.exit(f"Unknown Kokoro voice '{v['id']}' in {L['_file']}. See --list-voices.")
        if L.get("engine") == "piper" and not v.get("model"):
            sys.exit(f"Piper voice '{v['id']}' in {L['_file']} needs a \"model\" (e.g. de_DE-thorsten-high).")

    def say(self, L, v, text, wav):
        speed = L.get("speed", 1.0)
        if L.get("engine", "kokoro") == "piper":
            from piper import SynthesisConfig
            with wave.open(wav, "wb") as wf:
                self.piper(v["model"]).synthesize_wav(text, wf, syn_config=SynthesisConfig(length_scale=1.0 / speed))
        else:
            import soundfile as sf
            samples, rate = self.kokoro().create(text, voice=v["id"], speed=speed, lang=L["kokoro_lang"])
            sf.write(wav, samples, rate)


def encode(wav, mp3):
    os.makedirs(os.path.dirname(mp3), exist_ok=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", wav, "-af", FILTER,
                    "-ar", "24000", "-ac", "1", "-c:a", "libmp3lame", "-b:a", "40k", mp3], check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lang", help="language code(s), comma separated (default: all)")
    ap.add_argument("--voices", help="voice id(s), comma separated (default: all voices of the language)")
    ap.add_argument("--words", help="only these words, comma separated")
    ap.add_argument("--force", action="store_true", help="regenerate even if the MP3 exists")
    ap.add_argument("--list-voices", action="store_true")
    a = ap.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found. macOS: brew install ffmpeg")
    eng = Engines()
    if a.list_voices:
        print("Kokoro voices (prefix: a=US English, b=UK English, e=Spanish, f=French, i=Italian, p=Portuguese, h=Hindi, j=Japanese, z=Chinese; f/m = female/male):")
        print("  " + ", ".join(sorted(eng.kokoro().get_voices())))
        print("Piper voices: https://huggingface.co/rhasspy/piper-voices (use the model name, e.g. de_DE-thorsten-high)")
        return

    langs = load_wordlists(a.lang.split(",") if a.lang else None)
    only_v = set(a.voices.split(",")) if a.voices else None
    only_w = set(w.strip() for w in a.words.split(",")) if a.words else None
    made = skipped = 0
    with tempfile.TemporaryDirectory() as tmp:
        for L in langs:
            for v in L["voices"]:
                vid = v["id"]
                if only_v and vid not in only_v:
                    continue
                todo = [w for w in words_of(L) if (not only_w or w in only_w)]
                missing = [w for w in todo if a.force or not os.path.exists(audio_path(vid, w))]
                skipped += len(todo) - len(missing)
                if not missing:
                    continue
                eng.check(L, v)
                for w in missing:
                    text = L.get("pronounce", {}).get(w, w) + "."
                    wav = os.path.join(tmp, "w.wav")
                    eng.say(L, v, text, wav)
                    encode(wav, audio_path(vid, w))
                    made += 1
                    print(f"  {L['code']} {vid}: {w}", flush=True)
    print(f"Done: {made} generated, {skipped} already existed. Next: python3 tools/build.py")


if __name__ == "__main__":
    main()
