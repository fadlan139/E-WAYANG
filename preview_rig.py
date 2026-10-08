"""Pratinjau rig tanpa pygame (PIL saja): python tools/preview_rig.py bima_new"""
import json, math, sys
from pathlib import Path
from PIL import Image
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from rigmath import solve_arm

def render(name, target_local, scale=0.3, flip=False, tilt=0.0):
    d = ROOT / "assets" / "rig" / name
    rig = json.loads((d / "rig.json").read_text())
    body = Image.open(d / "body.png"); up = Image.open(d / "upper.png"); fo = Image.open(d / "fore.png")
    s = scale
    def sc(im): return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    body, up, fo = sc(body), sc(up), sc(fo)
    lu, lf = rig["len_upper"] * s, rig["len_fore"] * s
    M = int((lu + lf) * 1.05)
    canvas = Image.new("RGBA", (body.width + 2 * M, body.height + 2 * M), (0, 0, 0, 0))
    S = (rig["shoulder_on_body"][0] * s + M, rig["shoulder_on_body"][1] * s + M)
    th_u, th_f, E, Hd = solve_arm(target_local, lu, lf)
    ru, rf = math.radians(rig["rest_upper_angle"]), math.radians(rig["rest_fore_angle"])
    canvas.alpha_composite(body, (M, M))
    def paste_rot(img, pivot, at, ccw):
        w, h = img.size
        pad = int(math.hypot(w, h))
        big = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0)); big.paste(img, (pad, pad))
        rot = big.rotate(ccw, resample=Image.BICUBIC, center=(pad + pivot[0], pad + pivot[1]))
        canvas.alpha_composite(rot, (int(round(at[0] - pad - pivot[0])), int(round(at[1] - pad - pivot[1]))))
    Ep = (S[0] + E[0], S[1] + E[1])
    paste_rot(fo, (rig["fore"]["pivot"][0] * s, rig["fore"]["pivot"][1] * s), Ep, -math.degrees(th_f - rf))
    paste_rot(up, (rig["upper"]["pivot"][0] * s, rig["upper"]["pivot"][1] * s), S, -math.degrees(th_u - ru))
    if tilt: canvas = canvas.rotate(tilt, resample=Image.BICUBIC)
    if flip: canvas = canvas.transpose(Image.FLIP_LEFT_RIGHT)
    return canvas, (lu, lf)

if __name__ == "__main__":
    import json
    names = sys.argv[1:] or ["bima_new"]
    s = 0.22
    for name in names:
        rig = json.loads((ROOT / "assets/rig" / name / "rig.json").read_text())
        lu, lf = rig["len_upper"] * s, rig["len_fore"] * s
        R = (lu + lf) * 0.98
        hl, pv = rig["fore"]["hand_local"], rig["fore"]["pivot"]
        el, up = rig["upper"]["elbow_local"], rig["upper"]["pivot"]
        rest = ((el[0] - up[0]) + (hl[0] - pv[0]), (el[1] - up[1]) + (hl[1] - pv[1]))
        rest = (rest[0] * s, rest[1] * s)
        # arah depan di ruang lokal: kiri jika source_facing = -1, kanan jika 1
        f = -1 if rig["source_facing"] < 0 else 1
        poses = [("istirahat", rest), ("depan lurus", (f * R, 0)), ("depan atas", (f * R * .7, -R * .7)),
                 ("atas", (0, -R)), ("depan bawah", (f * R * .6, R * .6)), ("lipat", (f * R * .35, R * .1))]
        tiles = [render(name, t, s)[0] for _, t in poses]
        w, h = tiles[0].size
        sheet = Image.new("RGBA", (w * 3, h * 2), (235, 225, 200, 255))
        for i, t in enumerate(tiles):
            sheet.alpha_composite(t, ((i % 3) * w, (i // 3) * h))
        out = Path(f"/home/claude/rigprev_{name}.png"); sheet.convert("RGB").save(out); print(out, sheet.size)
