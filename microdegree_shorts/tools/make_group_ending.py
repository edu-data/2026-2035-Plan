"""엔딩용 3인 단체 이미지 합성 (쫑이·누나·뭉이가 한 장면에 함께)

입력: assets/cutouts/{jong,nuna,dog}_cut.png  — 기존 캐릭터 이미지에서 배경만 제거한 것
      (@imgly/background-removal-node 로 생성, 얼굴·의상은 원본 픽셀 그대로)
      assets/plates/jong.png — 배경(쫑이를 지우고 흐리게 처리해 보케 배경으로 사용)
출력: assets/plates/ending_group.png (720x1280)
"""
import os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "assets")
W, H = 720, 1280

def load_cut(name, y0, y1, fade=0):
    """잘라낸 캐릭터에서 y0~y1 구간만 사용(위 배지·아래 자막 제거), 하단은 부드럽게 페이드"""
    im = Image.open(os.path.join(A, "cutouts", f"{name}_cut.png")).convert("RGBA")
    a = np.asarray(im).copy()
    a[:y0, :, 3] = 0; a[y1:, :, 3] = 0
    if fade:
        for i, y in enumerate(range(y1 - fade, y1)):
            a[y, :, 3] = (a[y, :, 3] * (1 - i / fade)).astype(np.uint8)
    return Image.fromarray(a).crop((0, y0, 720, y1))

def place(canvas, im, scale, x, bottom, flip=False, shadow=True):
    if flip: im = im.transpose(Image.FLIP_LEFT_RIGHT)
    im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    y = bottom - im.height
    if shadow:  # 은은한 그림자로 배경과 붙어 보이게
        sh = Image.new("RGBA", im.size, (20, 10, 5, 0)); sh.putalpha(im.split()[3].point(lambda v: int(v * 0.45)))
        sh = sh.filter(ImageFilter.GaussianBlur(18))
        canvas.alpha_composite(sh, (x + 10, y + 12))
    canvas.alpha_composite(im, (x, y))
    return (x, y, im.width, im.height)

def background():
    """누나 원본 배경(어두운 웜톤)을 크게 흐려 전체 배경으로 사용 → 누나 이미지 가장자리가 자연스럽게 녹아듦"""
    src = Image.open(os.path.join(A, "plates", "nuna.png")).convert("RGB").transpose(Image.FLIP_LEFT_RIGHT)
    bg = src.crop((0, 75, 720, 1065)).resize((W, int(990 * W / 720 * 1.35)), Image.LANCZOS)
    bg = bg.crop((0, 0, W, H)) if bg.height >= H else bg.resize((W, H))
    bg = bg.filter(ImageFilter.GaussianBlur(28))
    bg = ImageEnhance.Brightness(bg).enhance(0.75).convert("RGBA")
    # 따뜻한 보케 조명 몇 개
    rng = np.random.default_rng(7); glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(glow)
    for _ in range(14):
        x, y, r = rng.integers(0, W), rng.integers(80, 900), rng.integers(18, 46)
        g.ellipse([x - r, y - r, x + r, y + r], fill=(255, 190, 120, int(rng.integers(25, 60))))
    bg.alpha_composite(glow.filter(ImageFilter.GaussianBlur(10)))
    yy, xx = np.mgrid[0:H, 0:W]; d = np.sqrt(((xx - W / 2) / (W * 0.8)) ** 2 + ((yy - H * 0.42) / (H * 0.75)) ** 2)
    dark = Image.new("RGBA", (W, H), (12, 6, 3, 0)); dark.putalpha(Image.fromarray((np.clip(d, 0, 1) ** 2 * 140).astype(np.uint8)))
    bg.alpha_composite(dark)
    return bg

def fade_bottom(im, start_frac, end_frac=1.0):
    a = np.asarray(im).copy(); h = a.shape[0]; y0, y1 = int(h * start_frac), int(h * end_frac)
    ramp = np.ones(h); ramp[y0:y1] = np.linspace(1, 0, y1 - y0); ramp[y1:] = 0
    a[:, :, 3] = (a[:, :, 3] * ramp[:, None]).astype(np.uint8)
    return Image.fromarray(a)

def tag(d, x, y, text, color):
    f = ImageFont.truetype(os.path.join(A, "fonts", "Pretendard-SemiBold.otf"), 17)
    tw = d.textlength(text, font=f)
    d.rounded_rectangle([x, y, x + tw + 20, y + 28], radius=6, fill=(14, 22, 42, 215), outline=color, width=2)
    d.text((x + 10, y + 14), text, font=f, fill=color, anchor="lm")

def main():
    cv = background()
    BOTTOM = 1085  # 자막 상자(1074~) 뒤로 몸 아랫부분이 가려짐
    nuna = fade_bottom(load_cut("nuna", 75, 1065), 0.62, 0.98)
    jong = load_cut("jong", 75, 1105)
    dog = load_cut("dog", 190, 1032, fade=14)
    # 누나: 오른쪽 위 (좌우반전 → 고개가 쫑이 쪽으로, 잘린 머리 윗부분은 화면 맨 위에 맞춤)
    s_n = 0.74; place(cv, nuna, s_n, W - int(720 * s_n) + 20, int(990 * s_n), flip=True, shadow=False)
    # 쫑이: 왼쪽 앞
    s_j = 0.76; place(cv, jong, s_j, -64, BOTTOM)
    # 뭉이: 오른쪽 아래 앞줄
    s_d = 0.43; place(cv, dog, s_d, W - int(720 * s_d) + 6, BOTTOM - 4)
    d = ImageDraw.Draw(cv)
    tag(d, 24, 345, "남주 쫑이", (56, 186, 246))
    tag(d, W - 128, 92, "여주 누나", (240, 113, 178))
    tag(d, W - 150, 640, "댕댕이 뭉이", (251, 190, 38))
    out = os.path.join(A, "plates", "ending_group.png")
    cv.convert("RGB").save(out); print("saved", out)

if __name__ == "__main__":
    main()
