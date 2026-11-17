import os
import sys
import io
import json
import time
import wave
import shutil
import threading
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from google.genai import types

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

ENV_CANDIDATES = [
    r"c:\Users\mattu\Documents\MyProjects\🤖_AgentTools\Scripts\.env",
    r"c:\Users\mattu\Documents\MyProjects\.env",
]
for env_path in ENV_CANDIDATES:
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

project_id = (
    os.getenv("CONSTRUCTION_GCP_PROJECT_ID")
    or os.getenv("PERSONAL_AI_PROJECT_ID")
    or os.getenv("VERTEX_AI_PROJECT_ID")
)
cred = (
    os.getenv("CONSTRUCTION_GOOGLE_APPLICATION_CREDENTIALS")
    or os.getenv("PERSONAL_AI_CREDENTIALS")
    or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
)
for p in [
    r"c:\Users\mattu\Documents\MyProjects\🤖_AgentTools\Scripts\Config\personal_key.json",
    r"c:\Users\mattu\Documents\MyProjects\🤖_AgentTools\Config\personal_key.json",
    r"C:\AgentTools\Config\personal_key.json",
]:
    if (not cred or not os.path.exists(cred)) and os.path.exists(p):
        cred = p
if cred and os.path.exists(cred):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred

TTS_MODEL = "gemini-3.8-flash-tts"
client = genai.Client(vertexai=True, project=project_id, location="global")

PROJECT_ROOT = r"c:\Users\mattu\Documents\MyProjects\pokemon-games"
AUDIO_DIR = os.path.join(PROJECT_ROOT, "assets", "audio")
CRIES_DIR = os.path.join(AUDIO_DIR, "cries")
SUMMON_DIR = os.path.join(AUDIO_DIR, "summon")
LEADERS_DIR = os.path.join(AUDIO_DIR, "leaders")
SYS_DIR = os.path.join(AUDIO_DIR, "sys")
TEMP_DIR = os.path.join(PROJECT_ROOT, "scripts", "_temp_tts")
PROGRESS_PATH = os.path.join(TEMP_DIR, "progress.json")

for d in [SUMMON_DIR, LEADERS_DIR, SYS_DIR, TEMP_DIR]:
    os.makedirs(d, exist_ok=True)

# Import MAIN_75 from build_pokemon_assets
sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))
from build_pokemon_assets import MAIN_75

RATE_LOCK = threading.Lock()
LAST_CALL_TS = 0.0
MIN_GAP = 0.85  # ~70 RPM safe pacing across threads

def pace_call():
    global LAST_CALL_TS
    with RATE_LOCK:
        now = time.time()
        wait = MIN_GAP - (now - LAST_CALL_TS)
        if wait > 0:
            time.sleep(wait)
        LAST_CALL_TS = time.time()

SATOSHI_VOICE = "Puck"
SATOSHI_FX = "rubberband=pitch=1.08:formant=shifted:pitchq=quality:smoothing=on"

ROTOM_VOICE = "Puck"
ROTOM_FX = "rubberband=pitch=1.16:formant=shifted:pitchq=quality:smoothing=on"

def extract_pcm(audio_bytes):
    if audio_bytes[:4] == b"RIFF":
        with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
            pcm = wf.readframes(wf.getnframes())
    else:
        pcm = audio_bytes
    if len(pcm) % 2 != 0:
        pcm = pcm[:-1]
    return pcm

def mp3_to_pcm24k(mp3_path):
    if not os.path.exists(mp3_path):
        return b""
    out = subprocess.check_output(
        ["ffmpeg", "-v", "error", "-i", mp3_path, "-ar", "24000", "-ac", "1", "-f", "s16le", "-"]
    )
    if len(out) % 2 != 0:
        out = out[:-1]
    return out

def apply_fx_to_pcm(pcm_bytes, af_filter, tag="fx"):
    if not af_filter:
        return pcm_bytes
    in_w = os.path.join(TEMP_DIR, f"{tag}_{threading.get_ident()}.wav")
    with wave.open(in_w, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(pcm_bytes)
    try:
        out_pcm = subprocess.check_output(
            ["ffmpeg", "-v", "error", "-y", "-i", in_w, "-af", af_filter, "-ar", "24000", "-ac", "1", "-f", "s16le", "-"]
        )
    finally:
        if os.path.exists(in_w):
            os.remove(in_w)
    if len(out_pcm) % 2 != 0:
        out_pcm = out_pcm[:-1]
    return out_pcm

def pcm_to_mp3(pcm_bytes, mp3_path, bitrate="56k"):
    in_w = os.path.join(TEMP_DIR, f"enc_{threading.get_ident()}_{int(time.time()*1000)}.wav")
    with wave.open(in_w, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(pcm_bytes)
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", in_w, "-ar", "24000", "-ac", "1", "-b:a", bitrate, mp3_path],
            check=True,
        )
    finally:
        if os.path.exists(in_w):
            os.remove(in_w)

def synth_ja(voice_name, text_ja, af_filter=None, max_sec=16.0):
    # Pure Japanese text prompt prevents any English header leakage!
    backoff = [4, 10, 22, 40, 65]
    for attempt in range(len(backoff) + 1):
        try:
            pace_call()
            resp = client.models.generate_content(
                model=TTS_MODEL,
                contents=text_ja,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
                        )
                    ),
                ),
            )
            raw_pcm = extract_pcm(resp.candidates[0].content.parts[0].inline_data.data)
            dur = len(raw_pcm) / 48000.0
            if (dur > max_sec or dur < 0.5) and attempt < len(backoff):
                continue
            return apply_fx_to_pcm(raw_pcm, af_filter)
        except Exception as e:
            err_s = str(e)
            if attempt < len(backoff):
                w = backoff[attempt] if ("429" in err_s or "RESOURCE_EXHAUSTED" in err_s) else 5
                print(f"    [Retry {attempt+1}] {err_s[:70]} -> sleep {w}s", flush=True)
                time.sleep(w)
            else:
                raise

SYS_CLIPS = [
    ("test", 25, "ピカチュウ、じゅんびバッチリだぜ！ ポケモン わくわくゲームランド、いっくぞー！ ポケモン、ゲットだぜ！！"),
    ("hit", None, "やったぜ！ カードのポケモン、ゲットだぜ！！"),
    ("double_hit", None, "すっげぇー！ ダブルゲットだぜ！！"),
    ("triple_hit", None, "うおおぉっ！ ぜんいん どうじゲット！ マスターボールきゅうの かみびきだぜ！！"),
    ("reach", None, "きたきたぁっ！ リーチだぜ！ あと いっぴきで ポケモンビンゴ たっせいだ！！"),
    ("bingo", 25, "やったぁぁー！！ ポケモンマスターきゅう！ ビンゴたっせい、ゲットだぜぇぇ！！"),
    ("reset", None, "モンスターボール リセット！ あたらしい ポケモンカードで ぼうけんスタートだぜ！！"),
    ("complete", 25, "ぜん ななじゅうごひきの ポケモンが だいしゅうけつしたぞ！ さいこうの ポケモンマスターだ！！"),
    ("sagase_start", 25, "ポケモンを さがせ！ かくれている ポケモンたちを ぜんいん みつけだそうぜ！！"),
    ("sagase_clear", 151, "すっげぇー！ かくれていた ポケモンを ぜんいん みつけたぞ！ パーフェクトだぜ！！"),
    ("memory_pair", None, "ナイスペア！ キラカード ゲットだぜ！！"),
    ("memory_clear", 25, "やったー！ すべての ポケモンカードを そろえたぞ！ きおくりょくマスターだぜ！！"),
]

LEADERS_12 = [
    ("pikachu", 25, SATOSHI_VOICE, SATOSHI_FX,
     "いっくぞ あいぼう ピカチュウ！ じゅうまんボルトで いちばんのりビンゴを ゲットだぜ！！",
     "やったぁぁー！！ ピカチュウの じゅうまんボルト さくれつ！ さいきょうの ビンゴたっせいだぜ！！"),
    ("charizard", 6, SATOSHI_VOICE, SATOSHI_FX,
     "いけっ リザードン！ しゃくねつの ブラストバーンで しょうりを つかみとるぜ！！",
     "うおおぉっ！ リザードンの ほのおが もえあがる！ かんぜんしょうり ビンゴだぜ！！"),
    ("eevee", 133, "Laomedeia", None,
     "イーブイの カードだね！ むげんの しんかパワーで キラキラビンゴを めざすよ！！",
     "やったぁー！！ イーブイと いっしょに ハッピービンゴ かんぜんたっせいだよ！！"),
    ("mewtwo", 150, "Charon", "rubberband=pitch=0.96:formant=preserved:pitchq=quality",
     "わたしは ミュウツー… さいきょうの サイコパワーで しょうりの みらいを みせてやろう。",
     "みごとだ… これぞ さいきょうの ちからが みちびきだした かんぺきなる ビンゴだ！"),
    ("mew", 151, "Achernar", "rubberband=pitch=1.06:formant=shifted:pitchq=quality:smoothing=on",
     "わぁっ、まぼろしの ミュウのカードだよ！ ゆびをふるで ミラクルを おこしちゃおう！",
     "すごいすごーい！！ ミュウの ミラクルパワーで キラキラビンゴ だいせいこうだね！！"),
    ("lucario", 448, "Iapetus", "rubberband=pitch=1.02:formant=preserved:pitchq=quality",
     "はどうは われにあり！ ルカリオとともに しょうりの はどうを つかみとるぞ！",
     "みごとな はどうの きょうめいだ！ はどうだんビンゴ、かんぜんたっせいだ！！"),
    ("greninja", 658, "Achird", "rubberband=pitch=1.03:formant=preserved:pitchq=quality",
     "いけっ ゲッコウガ！ キズナげんしょうの みずしゅりけんで さいそくビンゴを きめるぜ！",
     "しゅばっ！ めにも とまらぬ ちょうスピード！ みずしゅりけんビンゴ たっせいだぜ！！"),
    ("rayquaza", 384, "Algenib", "rubberband=pitch=0.95:formant=preserved:pitchq=quality",
     "てんくうの はしゃ レックウザ こうりん！ ガリョウテンセイで ちょうてんへ かけあがるぞ！！",
     "うおおぉっ！ おおぞらを つらぬく レックウザの ちょうぜつビンゴ たっせいだァァ！！"),
    ("sylveon", 700, "Laomedeia", "rubberband=pitch=1.04:formant=shifted:pitchq=quality:smoothing=on",
     "ニンフィアの カードね！ リボンの フェアリーパワーで すてきな ミラクルを おこすわよ！",
     "きらきら だいせいこう〜！！ ニンフィアの ムーンフォースで さいこうに かわいいビンゴよ！！"),
    ("gengar", 94, "Zubenelgenubi", "rubberband=pitch=1.05:formant=shifted:pitchq=quality:smoothing=on",
     "ケケケッ！ ゲンガーの カードとは いいセンスだねぇ！ シャドーボールで おどろかせちゃうぞ！",
     "イッヒッヒ！！ びっくり だいぎゃくてん！ ゲンガーの ゴーストビンゴ だいせいこうだぜ！！"),
    ("mimikyu", 778, "Achernar", None,
     "ミミッキュの カードを えらんでくれて ありがとう！ なかよしパワーで いっしょに がんばるね！",
     "やったぁ…！ ミミッキュも おおよろこびだよ！ さいこうの フレンドビンゴ たっせいだね！！"),
    ("piplup", 393, "Laomedeia", "rubberband=pitch=1.05:formant=shifted:pitchq=quality:smoothing=on",
     "むねを はって いっくよー！ ポッチャマの バブルこうせんで いちばんのりを めざそうね！！",
     "やったね ポッチャマ！！ キラキラの みずしぶきで パーフェクトビンゴ たっせいだよ！！"),
]

CALL_PREFIXES = [
    "いけっモンスターボール！",
    "とびだせ！",
    "でたぁっ！",
    "よっしゃあ！",
    "ポケモン ゲットだぜ！",
]

def col_letter_ja(num_id):
    return ["ビー", "アイ", "エヌ", "ジー", "オー"][(num_id - 1) // 15]

def main():
    manifest_path = os.path.join(AUDIO_DIR, "manifest.json")
    manifest = {"summon": {}, "leaders": {}, "sys": {}}
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception:
            pass

    ver = "v=1"
    short_gap = b"\x00" * int(24000 * 2 * 0.22)
    mid_gap = b"\x00" * int(24000 * 2 * 0.30)

    print("=== Phase 1: Generating 12 System Voice Clips ===", flush=True)
    for key, cry_dex, text in SYS_CLIPS:
        mp3_abs = os.path.join(SYS_DIR, f"{key}.mp3")
        if os.path.exists(mp3_abs) and os.path.getsize(mp3_abs) > 1000 and key in manifest["sys"]:
            continue
        pcm_voice = synth_ja(SATOSHI_VOICE, text, SATOSHI_FX, max_sec=14.0)
        if cry_dex:
            cry_pcm = mp3_to_pcm24k(os.path.join(CRIES_DIR, f"dex_{cry_dex}.mp3"))
            full_pcm = cry_pcm + short_gap + pcm_voice
        else:
            full_pcm = pcm_voice
        pcm_to_mp3(full_pcm, mp3_abs)
        manifest["sys"][key] = {
            "src": f"assets/audio/sys/{key}.mp3?{ver}",
            "duration": round(len(full_pcm) / 48000.0, 2),
        }
        print(f"  [Sys] {key} done ({manifest['sys'][key]['duration']}s)", flush=True)

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print("=== Phase 2: Generating 12 Partner Leader Voices (24 clips) ===", flush=True)
    for lid, dex_id, voice, fx, sel_t, bin_t in LEADERS_12:
        sel_p = os.path.join(LEADERS_DIR, f"{lid}_select.mp3")
        bin_p = os.path.join(LEADERS_DIR, f"{lid}_bingo.mp3")
        if os.path.exists(sel_p) and os.path.exists(bin_p) and lid in manifest["leaders"]:
            continue
        cry_pcm = mp3_to_pcm24k(os.path.join(CRIES_DIR, f"dex_{dex_id}.mp3"))
        pcm_sel = cry_pcm + short_gap + synth_ja(voice, sel_t, fx, max_sec=15.0)
        pcm_to_mp3(pcm_sel, sel_p)
        pcm_bin = cry_pcm + short_gap + synth_ja(voice, bin_t, fx, max_sec=15.0)
        pcm_to_mp3(pcm_bin, bin_p)
        manifest["leaders"][lid] = {
            "select": f"assets/audio/leaders/{lid}_select.mp3?{ver}",
            "bingo": f"assets/audio/leaders/{lid}_bingo.mp3?{ver}",
        }
        print(f"  [Leader] {lid} done", flush=True)

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print("=== Phase 3: Generating 75 Summon + Real Cry + Rotom Pokedex Voices ===", flush=True)

    def build_one_summon(row):
        bid, dex_id, name, rarity, type_key, type_label, emoji, move, quote, spoken_quote = row
        sid = f"{bid:02d}"
        mp3_abs = os.path.join(SUMMON_DIR, f"{sid}.mp3")
        if os.path.exists(mp3_abs) and os.path.getsize(mp3_abs) > 1500 and str(bid) in manifest["summon"]:
            return bid, manifest["summon"][str(bid)]

        col_ja = col_letter_ja(bid)
        prefix = CALL_PREFIXES[(bid - 1) % len(CALL_PREFIXES)]
        trainer_call = f"{prefix} {col_ja}の {bid}ばん、{name}だぜ！！"

        pcm_call = synth_ja(SATOSHI_VOICE, trainer_call, SATOSHI_FX, max_sec=10.0)
        cry_pcm = mp3_to_pcm24k(os.path.join(CRIES_DIR, f"dex_{dex_id}.mp3"))
        pcm_rotom = synth_ja(ROTOM_VOICE, f"{name}！ {spoken_quote}", ROTOM_FX, max_sec=15.0)

        # Layout: [Trainer Call] + mid_gap + [Official Cry] + short_gap + [Rotom Pokedex]
        # splitSec points right before [Official Cry], and quickEndSec points right after [Official Cry]!
        split_sec = round((len(pcm_call) + int(len(mid_gap) * 0.7)) / 48000.0, 2)
        quick_end_sec = round((len(pcm_call) + len(mid_gap) + len(cry_pcm) + int(len(short_gap) * 0.5)) / 48000.0, 2)
        full_pcm = pcm_call + mid_gap + cry_pcm + short_gap + pcm_rotom
        total_sec = round(len(full_pcm) / 48000.0, 2)

        pcm_to_mp3(full_pcm, mp3_abs)
        entry = {
            "src": f"assets/audio/summon/{sid}.mp3?{ver}",
            "splitSec": split_sec,
            "quickEndSec": quick_end_sec,
            "duration": total_sec,
            "dexId": dex_id,
        }
        return bid, entry

    done_cnt = 0
    with ThreadPoolExecutor(max_workers=3) as pool:
        futs = [pool.submit(build_one_summon, r) for r in MAIN_75]
        for fut in as_completed(futs):
            bid, entry = fut.result()
            manifest["summon"][str(bid)] = entry
            done_cnt += 1
            if done_cnt % 10 == 0 or done_cnt == len(MAIN_75):
                print(f"  [Summon] {done_cnt}/{len(MAIN_75)} completed", flush=True)
                with open(manifest_path, "w", encoding="utf-8") as f:
                    json.dump(manifest, f, ensure_ascii=False, indent=2)

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    shutil.rmtree(TEMP_DIR, ignore_errors=True)
    print("=== ALL POKEMON VOICES + CRIES GENERATED SUCCESSFULLY! ===", flush=True)

if __name__ == "__main__":
    main()
