"""마이크로디그리 웹드라마 쇼츠 생성기 — 「데이터는 설레고, 너는 촉촉해 #N」

사용법:
    python3 microdegree_shorts/tools/make_short.py microdegree_shorts/episodes/ep05.json

에피소드 JSON(대사·카드·타이밍)만 바꾸면 같은 스타일의 30초 쇼츠가 만들어진다.
단계: ① edge-tts로 대사 녹음 → ② BGM 합성 → ③ PIL로 프레임 합성 → ④ ffmpeg 믹싱/인코딩
필요: ffmpeg, Pillow, numpy, edge-tts(pip), speech.platform.bing.com 접속
"""
import json, os, subprocess, sys, tempfile, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # microdegree_shorts/
ASSETS = os.path.join(ROOT, "assets")
W, H, FPS = 720, 1280, 30

BLUE = (56, 186, 246); PINK = (240, 113, 178); YELLOW = (251, 190, 38)
ORANGE = (236, 160, 70); WHITE = (245, 247, 250); BG = (14, 22, 40)
CARD = (27, 40, 57); DIV = (70, 83, 100); GREY = (150, 160, 178); MINT = (120, 230, 190)
CARD_COLORS = [BLUE, PINK, YELLOW]
SPK_COLOR = {"누나": PINK, "쫑이": BLUE, "뭉이": ORANGE}
VOICE = {  # 화자별 기본 음성
    "누나": dict(voice="ko-KR-SunHiNeural", rate="+8%", pitch="+0Hz"),
    "뭉이": dict(voice="ko-KR-SunHiNeural", rate="+20%", pitch="+60Hz"),
    "쫑이": dict(voice="ko-KR-InJoonNeural", rate="+15%", pitch="+0Hz"),
}
# 장면 → 배경 이미지 (3강 영상에서 추출한 캐릭터 원본)
PLATE = {"nuna": "nuna", "dog": "dog", "jong": "jong", "end": "ending"}
XF = 0.4  # 장면 전환 크로스페이드(초)

_fonts = {}
def F(weight, size):
    key = (weight, size)
    if key not in _fonts:
        path = (os.path.join(ASSETS, "fonts", "D2Coding-Bold.ttf") if weight == "Mono"
                else os.path.join(ASSETS, "fonts", f"Pretendard-{weight}.otf"))
        _fonts[key] = ImageFont.truetype(path, size)
    return _fonts[key]

# ───────────────────────── 그래픽 요소 ─────────────────────────
def heart(d, cx, cy, r, color):
    d.ellipse([cx - r, cy - r * 0.9, cx, cy + r * 0.1], fill=color)
    d.ellipse([cx, cy - r * 0.9, cx + r, cy + r * 0.1], fill=color)
    d.polygon([(cx - r * 0.97, cy - 0.25 * r), (cx + r * 0.97, cy - 0.25 * r), (cx, cy + r * 0.95)], fill=color)

def badge(img, text, with_heart=True):
    d = ImageDraw.Draw(img); f = F("Medium", 17)
    tw = d.textlength(text, font=f)
    w = max(tw + (30 if with_heart else 0) + 34, 380)
    x0 = (W - w) / 2; y0, y1 = 21, 66; cx = W / 2
    d.rounded_rectangle([x0, y0, x0 + w, y1], radius=11, fill=(14, 22, 42), outline=BLUE, width=2)
    if with_heart:
        tx = cx - (tw + 24) / 2
        heart(d, tx + 7, (y0 + y1) / 2 + 1, 7, (244, 80, 140))
        d.text((tx + 24, (y0 + y1) / 2), text, font=f, fill=WHITE, anchor="lm")
    else:
        d.text((cx, (y0 + y1) / 2), text, font=f, fill=WHITE, anchor="mm")

def subtitle(img, speaker, lines, top=None):
    """화면 하단 자막 상자. top을 지정하면 원본 자막 상자를 완전히 덮을 수 있다."""
    d = ImageDraw.Draw(img); fl = F("Medium", 22); ft = F("SemiBold", 27)
    lh, bottom = 40, 1258
    if top is None:
        top = bottom - (58 + lh * len(lines)) - 6
    d.rounded_rectangle([20, top, 700, bottom], radius=14, fill=(18, 26, 42), outline=(58, 70, 92), width=1)
    d.text((44, top + 14), f"[{speaker}]", font=fl, fill=SPK_COLOR[speaker])
    avail = bottom - top - 46 - 10
    y = top + 46 + (avail - lh * len(lines)) / 2 + lh / 2
    for ln in lines:
        d.text((W / 2, y), ln, font=ft, fill=WHITE, anchor="mm"); y += lh

# 원본 이미지에 박혀 있는 자막 상자의 윗변(이보다 위에서 시작해야 가려짐)
MIN_TOP = {"nuna": 1070, "dog": 1110, "jong": 1110, "end": 1074}

def char_scene(ep, sc):
    im = Image.open(os.path.join(ASSETS, "plates", PLATE[sc["scene"]] + ".png")).convert("RGB")
    badge(im, ep["badge"])
    n = len(sc["lines"]); auto_top = 1258 - (58 + 40 * n) - 6
    subtitle(im, sc["speaker"], sc["lines"], top=min(auto_top, MIN_TOP[sc["scene"]]))
    return im

def info_base(ep, sc):
    info = sc["info"]
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    badge(im, info["badge"], with_heart=False)
    d.text((W / 2, 148), info["title"], font=F("Bold", 36), fill=BLUE, anchor="mm")
    d.text((W / 2, 196), info["subtitle"], font=F("Regular", 21), fill=(200, 208, 222), anchor="mm")
    d.text((W / 2, 1036), ep.get("footer", "경인교육대학교 김종민 교수 마이크로디그리"), font=F("Regular", 20), fill=GREY, anchor="mm")
    subtitle(im, sc["speaker"], sc["lines"], top=1118)
    return im

def card_img(i, card):
    col = CARD_COLORS[i]; cw, ch = 642, 220
    c = Image.new("RGBA", (cw, ch), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=16, fill=CARD + (255,), outline=col, width=2)
    d.rounded_rectangle([24, 27, 85, 72], radius=8, fill=col)
    d.text((54.5, 50), f"{i + 1:02d}", font=F("SemiBold", 24), fill=(20, 28, 44), anchor="mm")
    # 제목: `백틱` 구간은 코드 폰트(D2Coding)로 — Pretendard는 "<-"를 화살표 합자로 바꿔 버림
    x = 106
    for j, seg in enumerate(card["head"].split("`")):
        if not seg: continue
        f, colr = (F("Mono", 28), MINT) if j % 2 else (F("SemiBold", 28), WHITE)
        d.text((x, 50), seg, font=f, fill=colr, anchor="lm"); x += d.textlength(seg, font=f)
    d.line([24, 94, cw - 24, 94], fill=DIV, width=1)
    if card.get("code"):  # 코드 칩 + 설명 한 줄
        d.rounded_rectangle([24, 108, cw - 24, 152], radius=8, fill=(12, 18, 32), outline=(48, 60, 84))
        d.text((40, 130), card["code"], font=F("Mono", 24), fill=MINT, anchor="lm")
        if card.get("result"):
            d.text((cw - 40, 130), card["result"], font=F("Mono", 22), fill=(255, 214, 110), anchor="rm")
        d.text((24, 184), card["body"], font=F("Regular", 21), fill=(222, 228, 238), anchor="lm")
    else:
        d.text((24, 147), card["body"], font=F("Regular", 22), fill=(222, 228, 238), anchor="lm")
    return c

# ───────────────────────── 오디오 ─────────────────────────
def tts(sc, out_wav, tmp):
    v = dict(VOICE[sc["speaker"]]); v.update(sc.get("voice", {}))
    mp3 = os.path.join(tmp, os.path.basename(out_wav) + ".mp3")
    cmd = ["edge-tts", "--voice", v["voice"], f"--rate={v['rate']}", f"--pitch={v['pitch']}",
           "--text", sc.get("tts", " ".join(sc["lines"])), "--write-media", mp3]
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if proxy: cmd[1:1] = ["--proxy", proxy]
    subprocess.run(cmd, check=True, capture_output=True)
    trim = "silenceremove=start_periods=1:start_threshold=-45dB,areverse," * 2
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp3, "-af", trim.rstrip(","), "-ar", "44100", "-ac", "1", out_wav], check=True)
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out_wav],
                                capture_output=True, text=True).stdout)

def pauses(wav):
    """대사 속 쉼(쉼표) 끝 시점들 — 카드 등장 타이밍 자동 동기화용"""
    r = subprocess.run(["ffmpeg", "-i", wav, "-af", "silencedetect=n=-38dB:d=0.12", "-f", "null", "-"], capture_output=True, text=True)
    return [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", r.stderr)]

def bgm(path, dur, seed=1):
    SR = 44100; beat = 60 / 84
    t = np.arange(int(SR * dur)); out = np.zeros(len(t))
    def note(f, start, length, amp):
        s = int(start * SR)
        if s >= len(out): return
        tt = np.arange(min(int(length * SR), len(out) - s)) / SR
        env = np.exp(-tt * 2.2) * (1 - np.exp(-tt * 80))
        w = np.sin(2*np.pi*f*tt) + 0.35*np.sin(4*np.pi*f*tt)*np.exp(-tt*4) + 0.12*np.sin(6*np.pi*f*tt)*np.exp(-tt*6)
        out[s:s + len(tt)] += amp * env * w
    m = lambda k: 440 * 2 ** ((k - 69) / 12)
    prog = [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [55, 60, 62, 65]]  # Fmaj7-Em7-Dm7-G7sus
    bar = 4 * beat; i = 0; st = 0.0
    while st < dur:
        ch = prog[i % 4]; note(m(ch[0] - 12), st, bar * 1.2, 0.22)
        for k, b in enumerate([0, 1.5, 2, 3]):
            for nn in ch[1:]: note(m(nn), st + b * beat + 0.012 * k, beat * 2.5, 0.07 if b else 0.09)
        mel = [ch[3] + 12, ch[2] + 12, ch[1] + 12, ch[2] + 12]
        for k, b in enumerate([0.5, 1.5, 2.5, 3.5]):
            if (i + k + seed) % 3 != 2: note(m(mel[k]), st + b * beat, beat * 1.5, 0.05)
        st += bar; i += 1
    rng = np.random.default_rng(seed); hh = np.zeros(len(out))
    for b in np.arange(0.5, dur / beat, 1.0):
        s = int(b * beat * SR); n = int(0.08 * SR)
        if s + n < len(hh): hh[s:s + n] += rng.normal(0, 1, n) * np.exp(-np.arange(n) / SR * 60) * 0.02
    out += np.diff(hh, prepend=0)
    for d_, g in [(0.031, 0.3), (0.047, 0.25), (0.089, 0.2), (0.13, 0.15)]:
        k = int(d_ * SR); out[k:] += g * out[:-k]
    out /= np.abs(out).max() * 1.05
    fi, fo = int(0.8 * SR), int(1.5 * SR); out[:fi] *= np.linspace(0, 1, fi); out[-fo:] *= np.linspace(1, 0, fo)
    import wave
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())

# ───────────────────────── 메인 ─────────────────────────
def ease(x):
    x = min(max(x, 0.0), 1.0); return 1 - (1 - x) ** 3

def main(cfg_path, out_path=None):
    ep = json.load(open(cfg_path, encoding="utf8"))
    dur = ep.get("duration", 30.0)
    out_path = out_path or os.path.join(ROOT, f"microdegree_ep{ep['episode']:02d}_shorts.mp4")
    tmp = tempfile.mkdtemp(prefix="mdshort_")
    scenes = ep["scenes"]

    # 1) 음성
    for k, sc in enumerate(scenes):
        sc["_wav"] = os.path.join(tmp, f"l{k}.wav"); sc["_len"] = tts(sc, sc["_wav"], tmp)
        print(f"  [{sc['speaker']}] {sc['_len']:.2f}s  {' '.join(sc['lines'])}")
    # 2) 타임라인: 장면 길이 = 음성 + 여유, 총합이 dur에 맞도록 여유를 배분
    lead = 0.35
    need = sum(sc["_len"] + lead for sc in scenes)
    spare = dur - need - 0.3
    if spare < 0:
        sys.exit(f"대사가 너무 깁니다: 음성 합계 {need:.1f}s > {dur}s. 문장을 줄이거나 rate를 올리세요.")
    weights = [sc.get("pad_weight", 1.0) for sc in scenes]; wsum = sum(weights)
    t = 0.0
    for sc, wgt in zip(scenes, weights):
        sc["_t0"] = t; sc["_voice_at"] = t + lead + (0.15 if t == 0 else 0)
        t += sc["_len"] + lead + spare * wgt / wsum
        sc["_t1"] = t
    scenes[-1]["_t1"] = dur
    # 인포그래픽 카드 등장 시점 = 쫑이 대사 쉼표에 맞춤
    for sc in scenes:
        if sc["scene"] == "info":
            ps = [p for p in pauses(sc["_wav"]) if 0.2 < p < sc["_len"] - 0.3]
            marks = [0.0] + ps
            sc["_card_t"] = [sc["_voice_at"] + (marks[i] if i < len(marks) else marks[-1] + 0.9 * (i - len(marks) + 1)) - 0.05 for i in range(3)]
    for sc in scenes:
        print(f"  {sc['scene']:5s} {sc['_t0']:5.2f}–{sc['_t1']:5.2f}s  voice@{sc['_voice_at']:.2f}")

    # 3) 영상
    static, cards = {}, {}
    for k, sc in enumerate(scenes):
        if sc["scene"] == "info":
            static[k] = info_base(ep, sc); cards[k] = [card_img(i, c) for i, c in enumerate(sc["info"]["cards"])]
        else:
            static[k] = char_scene(ep, sc)
    card_y = [262, 512, 762]

    def scene_frame(k, tt):
        sc = scenes[k]
        if sc["scene"] != "info": return static[k]
        im = static[k].copy()
        for i, c in enumerate(cards[k]):
            p = ease((tt - sc["_card_t"][i]) / 0.45)
            if p <= 0: continue
            if p < 1:
                c = c.copy(); c.putalpha(c.split()[3].point(lambda v: int(v * p)))
            im.paste(c, (39, int(card_y[i] + (1 - p) * 40)), c)
        return im

    def frame_at(tt):
        k = next((i for i, s in enumerate(scenes) if s["_t0"] <= tt < s["_t1"]), len(scenes) - 1)
        im = scene_frame(k, tt)
        if k > 0 and tt < scenes[k]["_t0"] + XF:
            im = Image.blend(scene_frame(k - 1, tt), im, (tt - scenes[k]["_t0"]) / XF)
        if tt > dur - 0.5:
            im = Image.blend(im, Image.new("RGB", (W, H)), (tt - (dur - 0.5)) / 0.5 * 0.6)
        return im

    if os.environ.get("PREVIEW"):
        for x in os.environ["PREVIEW"].split(","):
            frame_at(float(x)).save(os.path.join(tmp, f"prev_{float(x):05.1f}.png"))
        print("preview:", tmp); return
    vid = os.path.join(tmp, "video.mp4")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", vid], stdin=subprocess.PIPE)
    for i in range(int(dur * FPS)):
        p.stdin.write(frame_at(i / FPS).tobytes())
    p.stdin.close(); p.wait()

    # 4) 믹싱: 대사 + BGM(대사 나올 때 자동으로 줄어듦)
    bg = os.path.join(tmp, "bgm.wav"); bgm(bg, dur + 0.5, seed=ep["episode"])
    ins, fc, labels = ["-i", vid], [], []
    for k, sc in enumerate(scenes):
        ins += ["-i", sc["_wav"]]; ms = int(sc["_voice_at"] * 1000)
        fc.append(f"[{k + 1}]adelay={ms}|{ms},loudnorm=I={-17 if sc['speaker'] == '뭉이' else -16}:TP=-1.5[v{k}]"); labels.append(f"[v{k}]")
    nb = len(scenes) + 1; ins += ["-i", bg]
    fc.append("".join(labels) + f"amix=inputs={len(scenes)}:normalize=0:duration=longest,aresample=44100,apad=whole_dur={dur},asplit=2[vo][sc]")
    fc.append(f"[{nb}]volume=0.32,aresample=44100[bg];[bg][sc]sidechaincompress=threshold=0.03:ratio=4:attack=30:release=400[bgd]")
    fc.append(f"[vo][bgd]amix=inputs=2:normalize=0:duration=longest,alimiter=limit=0.9,atrim=0:{dur},afade=t=out:st={dur - 0.5}:d=0.5[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(fc), "-map", "0:v", "-map", "[a]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ac", "2", "-t", str(dur), "-movflags", "+faststart", out_path], check=True)
    print("완성:", out_path)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
