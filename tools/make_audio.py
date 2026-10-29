"""Generate the spoken word files with the open-source Kokoro voices.

    python3 tools/make_audio.py                 # every language, only words that have no MP3 yet
    python3 tools/make_audio.py --lang es       # one language
    python3 tools/make_audio.py --force         # redo everything (e.g. after changing speed)
    python3 tools/make_audio.py --words "Tide pool,Butte" --force   # redo some words
    python3 tools/make_audio.py --list-voices   # show the Kokoro voice ids

Needs:  pip install kokoro-onnx soundfile     and ffmpeg on the PATH (macOS: brew install ffmpeg).
The Kokoro model files (~350 MB) are downloaded to tools/models/ the first time.
Output: audio/<voice>/<word>.mp3 — trimmed, loudness-normalised, mono 24 kHz, 40 kbps.
"""
import argparse, os, shutil, subprocess, sys, tempfile, urllib.request
from common import TOOLS, load_wordlists, words_of, audio_path

MODELS = os.path.join(TOOLS, "models")
MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
MODEL_FILES = ["kokoro-v1.0.onnx", "voices-v1.0.bin"]

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

    try:
        import soundfile as sf
        from kokoro_onnx import Kokoro
    except ImportError:
        sys.exit("Missing packages. Run:  pip install kokoro-onnx soundfile")
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found. macOS: brew install ffmpeg")

    kokoro = Kokoro(*ensure_models())
    if a.list_voices:
        print("Kokoro voices (prefix: a=US English, b=UK English, e=Spanish, f=French, i=Italian, p=Portuguese, h=Hindi, j=Japanese, z=Chinese; f/m = female/male):")
        print("  " + ", ".join(sorted(kokoro.get_voices())))
        return

    langs = load_wordlists(a.lang.split(",") if a.lang else None)
    only_v = set(a.voices.split(",")) if a.voices else None
    only_w = set(w.strip() for w in a.words.split(",")) if a.words else None
    known = set(kokoro.get_voices())
    made = skipped = 0
    with tempfile.TemporaryDirectory() as tmp:
        for L in langs:
            for v in L["voices"]:
                vid = v["id"]
                if only_v and vid not in only_v:
                    continue
                if vid not in known:
                    sys.exit(f"Unknown Kokoro voice '{vid}' in {L['_file']}. See --list-voices.")
                for w in words_of(L):
                    if only_w and w not in only_w:
                        continue
                    out = audio_path(vid, w)
                    if os.path.exists(out) and not a.force:
                        skipped += 1
                        continue
                    text = L.get("pronounce", {}).get(w, w) + "."
                    samples, rate = kokoro.create(text, voice=vid, speed=L.get("speed", 1.0), lang=L["kokoro_lang"])
                    wav = os.path.join(tmp, "w.wav")
                    sf.write(wav, samples, rate)
                    encode(wav, out)
                    made += 1
                    print(f"  {L['code']} {vid}: {w}", flush=True)
    print(f"Done: {made} generated, {skipped} already existed. Next: python3 tools/build.py")


if __name__ == "__main__":
    main()
