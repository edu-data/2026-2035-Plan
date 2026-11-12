"""마이크로디그리 4강 쇼츠 렌더러: '데이터는 설레고, 너는 촉촉해 #4' (Posit Cloud)"""
import subprocess, sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
SCR = os.path.dirname(BASE)
FONT_DIR = os.path.join(SCR, "fonts/package/dist/public/static")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, "video_noaudio.mp4")
W, H, FPS, DUR = 720, 1280, 30, 30.0

def F(weight, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, f"Pretendard-{weight}.otf"), size)

BLUE = (56, 186, 246); PINK = (240, 113, 178); YELLOW = (251, 190, 38)
ORANGE = (236, 160, 70); WHITE = (245, 247, 250); BG = (14, 22, 40)
CARD = (27, 40, 57); DIV = (70, 83, 100); GREY = (150, 160, 178)

def plate(name):
    return Image.open(os.path.join(BASE, "plates", name + ".png")).convert("RGB")

# ---------- 공통 오버레이 ----------
def heart(d, cx, cy, r, color):
    d.ellipse([cx - r, cy - r * 0.9, cx, cy + r * 0.1], fill=color)
    d.ellipse([cx, cy - r * 0.9, cx + r, cy + r * 0.1], fill=color)
    d.polygon([(cx - r * 0.97, cy - 0.25 * r), (cx + r * 0.97, cy - 0.25 * r), (cx, cy + r * 0.95)], fill=color)

def badge(img, text, with_heart=True):
    d = ImageDraw.Draw(img)
    f = F("Medium", 17)
    tw = d.textlength(text, font=f)
    w = tw + (30 if with_heart else 0) + 34
    w = max(w, 380)
    x0 = (W - w) / 2; y0, y1 = 21, 66
    d.rounded_rectangle([x0, y0, x0 + w, y1], radius=11, fill=(14, 22, 42), outline=BLUE, width=2)
    cx = W / 2
    if with_heart:
        tx = cx - (tw + 24) / 2
        heart(d, tx + 7, (y0 + y1) / 2 + 1, 7, (244, 80, 140))
        d.text((tx + 24, (y0 + y1) / 2), text, font=f, fill=WHITE, anchor="lm")
    else:
        d.text((cx, (y0 + y1) / 2), text, font=f, fill=WHITE, anchor="mm")

SPK_COLOR = {"누나": PINK, "쫑이": BLUE, "뭉이": ORANGE}

def subtitle(img, speaker, lines, top=None):
    d = ImageDraw.Draw(img)
    fl = F("Medium", 22); ft = F("SemiBold", 27)
    lh = 40
    bottom = 1258
    if top is None:
        top = bottom - (58 + lh * len(lines)) - 6
    d.rounded_rectangle([20, top, 700, bottom], radius=14, fill=(18, 26, 42), outline=(58, 70, 92), width=1)
    d.text((44, top + 14), f"[{speaker}]", font=fl, fill=SPK_COLOR[speaker])
    avail = bottom - top - 46 - 10
    y = top + 46 + (avail - lh * len(lines)) / 2 + lh / 2
    for ln in lines:
        d.text((W / 2, y), ln, font=ft, fill=WHITE, anchor="mm")
        y += lh

TITLE = "데이터는 설레고, 너는 촉촉해 #4"

# ---------- 장면 정적 레이어 ----------
def scene_nuna():
    im = plate("nuna"); badge(im, TITLE)
    subtitle(im, "누나", ["쫑아… R 설치하다가 에러만 세 번째야.", "내 노트북으론 R 못 쓰는 거야?"], top=1070)
    return im

def scene_dog():
    im = plate("dog"); badge(im, TITLE)
    subtitle(im, "뭉이", ["(빨간 에러창 보며 갸우뚱)", "멍? 멍멍!"], top=1110)
    return im

def scene_jong():
    im = plate("jong"); badge(im, TITLE)
    subtitle(im, "쫑이", ["누나, 설치 안 해도 돼요! Posit Cloud면", "브라우저에서 바로 R을 써요!"], top=1110)
    return im

def scene_end():
    im = plate("ending"); badge(im, TITLE)
    subtitle(im, "쫑이", ["어때 누나! 촉촉해?", "Posit Cloud 실습은 저녁 4강 풀영상에서", "나랑 같이 해볼래?"])
    return im

CARDS = [
    ("01", BLUE, "posit.cloud 무료 가입", "구글·GitHub 계정으로 1분이면 가입 끝!"),
    ("02", PINK, "New Project → RStudio Project", "설치 없이 브라우저 안에 RStudio가 쫙!"),
    ("03", YELLOW, "데이터 업로드 & 코드 실행", "Upload로 CSV 올리고 Ctrl+Enter 한 방!"),
]

def info_base():
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    badge(im, "★ Posit Cloud로 R 시작하기 ★", with_heart=False)
    d.text((W / 2, 148), "설치 없이 R을 쓴다고?", font=F("Bold", 36), fill=BLUE, anchor="mm")
    d.text((W / 2, 196), "브라우저만 있으면 OK! 클라우드 R 3단계", font=F("Regular", 21), fill=(200, 208, 222), anchor="mm")
    d.text((W / 2, 1036), "경인교육대학교 김종민 교수 마이크로디그리", font=F("Regular", 20), fill=GREY, anchor="mm")
    subtitle(im, "쫑이", ["가입하고, 프로젝트 만들고, 데이터 올리면 끝!", "노트북 사양도 상관없어요."], top=1118)
    return im

def card_img(i):
    num, col, head, body = CARDS[i]
    cw, ch = 642, 220
    c = Image.new("RGBA", (cw, ch), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=16, fill=CARD + (255,), outline=col, width=2)
    d.rounded_rectangle([24, 27, 85, 72], radius=8, fill=col)
    d.text((54.5, 50), num, font=F("SemiBold", 24), fill=(20, 28, 44), anchor="mm")
    d.text((106, 50), head, font=F("SemiBold", 28), fill=WHITE, anchor="lm")
    d.line([24, 94, cw - 24, 94], fill=DIV, width=1)
    d.text((24, 147), body, font=F("Regular", 22), fill=(222, 228, 238), anchor="lm")
    return c

# ---------- 타임라인 ----------
# (시작, 끝, 장면) — 장면 간 0.4초 크로스페이드
XF = 0.4
SCENES = [(0.0, 7.2, "nuna"), (7.2, 9.4, "dog"), (9.4, 15.6, "jong"), (15.6, 22.8, "info"), (22.8, DUR, "end")]
CARD_T = [15.95, 16.95, 18.3]  # 대사 '가입하고 / 프로젝트 만들고 / 데이터 올리면'에 맞춤

static = {"nuna": scene_nuna(), "dog": scene_dog(), "jong": scene_jong(), "end": scene_end()}
ib = info_base(); cards = [card_img(i) for i in range(3)]
CARD_Y = [262, 512, 762]

def ease(x):
    x = min(max(x, 0.0), 1.0); return 1 - (1 - x) ** 3

def render_info(t):
    im = ib.copy()
    for i in range(3):
        p = ease((t - CARD_T[i]) / 0.45)
        if p <= 0: continue
        c = cards[i]
        if p < 1:
            a = c.split()[3].point(lambda v: int(v * p)); c = c.copy(); c.putalpha(a)
        im.paste(c, (39, int(CARD_Y[i] + (1 - p) * 40)), c)
    return im

def scene_frame(name, t, t0):
    if name == "info":
        return render_info(t)
    im = static[name]
    return im


def frame_at(t):
    cur = [s for s in SCENES if s[0] <= t < s[1]]
    s = cur[0] if cur else SCENES[-1]
    im = scene_frame(s[2], t, s[0])
    idx = SCENES.index(s)
    if idx > 0 and t < s[0] + XF:  # 이전 장면과 크로스페이드
        p = SCENES[idx - 1]
        prev = scene_frame(p[2], t, p[0])
        a = (t - s[0]) / XF
        im = Image.blend(prev, im, a)
    if t > DUR - 0.5:  # 마지막 페이드아웃
        im = Image.blend(im, Image.new("RGB", (W, H), (0, 0, 0)), (t - (DUR - 0.5)) / 0.5 * 0.6)
    return im

if __name__ == "__main__":
    if os.environ.get("PREVIEW"):
        for t in [float(x) for x in os.environ["PREVIEW"].split(",")]:
            frame_at(t).save(os.path.join(BASE, f"prev_{t:05.1f}.png"))
        sys.exit()
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        p.stdin.write(frame_at(i / FPS).tobytes())
    p.stdin.close(); p.wait()
    print("done", OUT)
