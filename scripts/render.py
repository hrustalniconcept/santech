#!/usr/bin/env python3
"""
Датский квартал — рендер вертикальных карточек 2:3 с чистыми планировками.

Карточка (телефонный формат 2:3, белый фон, фирменный стиль):
  - сверху логотип: «ХРУСТАЛЬНЫЙ ПАРК» (надзаголовок) + «Датский квартал» (Playfair Display)
  - акцентная черта #52358B
  - подпись «Дом №X · Квартира №Y · Z этаж» (Manrope)
  - по центру — чистая планировка на белом фоне

Шрифты: Playfair Display (заголовок) + Manrope (текст) из ../fonts.
Источник планировок: assets/plans_clean/<src>, перечень — scripts/clean_jobs.json.

Использование:
  python3 scripts/render.py                       # отрендерить все карточки из clean_jobs.json
  python3 scripts/render.py --only 03             # только карточку с id "03"
  python3 scripts/render.py --plan path --caption "Дом №4 · Квартира №3 · 1 этаж" --out card.png
"""
import argparse
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

# ---- пути ---------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "fonts")
PLANS_DIR = os.path.join(ROOT, "assets", "plans_clean")
OUT_DIR = os.path.join(ROOT, "outputs", "cards")
JOBS = os.path.join(ROOT, "scripts", "clean_jobs.json")

# ---- фирменный стиль ----------------------------------------------------
W, H = 1200, 1800                 # 2:3 вертикаль
ACCENT = (82, 53, 139)            # #52358B
INK = (28, 26, 34)                # почти чёрный заголовок
GREY = (90, 90, 100)             # подпись
BG = (255, 255, 255)

MARGIN = 96                       # боковые поля

PLAYFAIR = os.path.join(FONTS, "PlayfairDisplay.ttf")
MANROPE = os.path.join(FONTS, "Manrope.ttf")


def font(path, size, weight=None):
    f = ImageFont.truetype(path, size)
    if weight is not None:
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
    return f


def text_w(draw, s, fnt, tracking=0):
    if tracking == 0:
        return draw.textlength(s, font=fnt)
    return sum(draw.textlength(ch, font=fnt) for ch in s) + tracking * (len(s) - 1)


def draw_tracked(draw, xy, s, fnt, fill, tracking=0, anchor_center_x=None):
    """Рисует строку с трекингом. Если задан anchor_center_x — центрирует по нему."""
    total = text_w(draw, s, fnt, tracking)
    x, y = xy
    if anchor_center_x is not None:
        x = anchor_center_x - total / 2
    for ch in s:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += draw.textlength(ch, font=fnt) + tracking
    return total


def render_card(plan_path, caption, out_path):
    card = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(card)
    cx = W // 2

    # --- надзаголовок: ХРУСТАЛЬНЫЙ ПАРК ---
    f_eyebrow = font(MANROPE, 30, 700)
    y = 120
    draw_tracked(d, (0, y), "ХРУСТАЛЬНЫЙ ПАРК", f_eyebrow, ACCENT,
                 tracking=8, anchor_center_x=cx)

    # --- заголовок: Датский квартал (Playfair) ---
    f_title = font(PLAYFAIR, 92, 700)
    title = "Датский квартал"
    tb = d.textbbox((0, 0), title, font=f_title)
    y = 168
    d.text((cx - (tb[2] - tb[0]) / 2 - tb[0], y), title, font=f_title, fill=INK)

    # --- акцентная черта ---
    line_y = y + (tb[3] - tb[1]) + 60
    d.line([(cx - 70, line_y), (cx + 70, line_y)], fill=ACCENT, width=4)

    # --- подпись: Дом №X · Квартира №Y · Z этаж ---
    f_cap = font(MANROPE, 40, 600)
    cb = d.textbbox((0, 0), caption, font=f_cap)
    cap_y = line_y + 44
    d.text((cx - (cb[2] - cb[0]) / 2 - cb[0], cap_y), caption, font=f_cap, fill=GREY)
    cap_bottom = cap_y + (cb[3] - cb[1]) + 40

    # --- зона планировки ---
    footer_h = 110
    area_top = cap_bottom + 20
    area_bottom = H - footer_h
    area_w = W - 2 * MARGIN
    area_h = area_bottom - area_top

    plan = Image.open(plan_path).convert("RGBA")
    # белый фон под план (на случай прозрачности)
    bgp = Image.new("RGBA", plan.size, (255, 255, 255, 255))
    plan = Image.alpha_composite(bgp, plan).convert("RGB")

    scale = min(area_w / plan.width, area_h / plan.height)
    nw, nh = int(plan.width * scale), int(plan.height * scale)
    plan = plan.resize((nw, nh), Image.LANCZOS)
    px = cx - nw // 2
    py = area_top + (area_h - nh) // 2
    card.paste(plan, (px, py))

    # --- футер: акцентная точка-подпись ---
    f_foot = font(MANROPE, 24, 600)
    draw_tracked(d, (0, H - 70), "ХРУСТАЛЬНЫЙ  ПАРК", f_foot, (180, 180, 188),
                 tracking=4, anchor_center_x=cx)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    card.save(out_path, "PNG")
    return out_path


def caption_from_job(job):
    if job.get("caption"):
        return job["caption"]
    h, a, f = job.get("house"), job.get("apartment"), job.get("floor")
    return f"Дом №{h} · Квартира №{a} · {f} этаж"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="id карточки из clean_jobs.json")
    ap.add_argument("--plan", help="путь к планировке (одиночный режим)")
    ap.add_argument("--caption", help="подпись (одиночный режим)")
    ap.add_argument("--out", help="выходной файл (одиночный режим)")
    args = ap.parse_args()

    if args.plan:
        out = args.out or os.path.join(OUT_DIR, "card.png")
        render_card(args.plan, args.caption or "", out)
        print("OK", out)
        return

    with open(JOBS, encoding="utf-8") as fh:
        data = json.load(fh)
    jobs = data["cards"] if isinstance(data, dict) else data

    n = 0
    for job in jobs:
        if args.only and job.get("id") != args.only:
            continue
        src = job["src"]
        plan_path = os.path.join(PLANS_DIR, src)
        if not os.path.exists(plan_path):
            print(f"SKIP {job.get('id')}: нет файла {src}", file=sys.stderr)
            continue
        cap = caption_from_job(job)
        out = os.path.join(OUT_DIR, f"{job['id']}_{os.path.splitext(src)[0]}.png")
        render_card(plan_path, cap, out)
        print("OK", job.get("id"), cap)
        n += 1
    print(f"Готово карточек: {n}")


if __name__ == "__main__":
    main()
