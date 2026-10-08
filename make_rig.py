"""
Memecah aset wayang utuh menjadi bagian yang bisa digerakkan:
  body.png  = badan tanpa lengan depan
  upper.png = lengan atas (bahu -> siku)
  fore.png  = lengan bawah + tangan (siku -> ujung tangan)
  rig.json  = titik sendi (pivot) dan panjang tulang

Pakai:  python tools/make_rig.py            (semua karakter di RIGS)
        python tools/make_rig.py bima_new   (satu karakter)

Untuk wayang baru: tambahkan entri di RIGS. Koordinat memakai piksel pada
gambar yang SUDAH DIPOTONG ke area terlihat (bounding box alpha).
 - cut      : (x0, x1, y0, y1) garis potong di bahu supaya lengan terlepas
              dari badan (area kecil di sambungan bahu).
 - probe    : satu titik di dalam lengan, untuk memilih bagian lengan.
 - shoulder / elbow / hand : titik sendi di gambar utuh.
 - split_y  : tinggi tempat lengan dibagi jadi atas dan bawah (setinggi siku).
              Jika tidak diisi, lengan dibagi dengan garis tegak lurus arah bahu->siku.
 - poly     : (opsional) daftar titik poligon. Jika diisi, lengan = piksel di dalam
              poligon (dipakai bila lengan menyatu dengan badan sehingga 'cut' tidak cukup).
 - rod_anchor: (opsional) titik gapit badan pada gambar utuh.
 - erase    : (opsional) daftar poligon yang dihapus dari badan (mis. tongkat bawaan
              gambar yang menempel di tangan, karena tongkat digambar lewat kode).
 - keep_shoulder: (opsional) radius piksel sendi bahu yang dibiarkan di badan agar
              tidak ada celah saat lengan berputar.
 - body_rod : (opsional) False jika gambar sudah punya gapit badan sendiri.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

RIGS = {
    "bima_new": {
        "cut": (335, 338, 540, 650),
        "probe": (232, 1000),          # (x, y) di dalam lengan depan
        "shoulder": (298, 620),
        "elbow": (232, 1000),
        "hand": (70, 1420),
        "split_y": 1000,
        "overlap": 40,
        "source_facing": -1,
    },
    "werkudara_new": {
        "poly": [(205, 254), (246, 250), (246, 292), (250, 330), (205, 400), (196, 480),
                 (172, 545), (130, 592), (90, 602), (0, 602), (0, 380)],
        "erase": [[(86, 597), (100, 586), (186, 638), (186, 670), (165, 668)]],
        "shoulder": (232, 272),
        "elbow": (152, 430),
        "hand": (55, 578),
        "split_y": None,
        "overlap": 14,
        "keep_shoulder": 12,
        "body_rod": False,
        "source_facing": -1,
    },
    "arjuna_new": {
        "poly": [(96, 214), (140, 214), (140, 250), (137, 262), (137, 700), (30, 700), (30, 214)],
        "shoulder": (122, 236),
        "elbow": (122, 430),
        "hand": (80, 630),
        "split_y": None,
        "overlap": 14,
        "keep_shoulder": 14,
        "source_facing": -1,
    },
    "kapi_angeni": {
        "poly": [(455, 447), (700, 447), (700, 700), (455, 700)],
        "shoulder": (468, 462),
        "elbow": (503, 550),
        "hand": (630, 650),
        "split_y": None,
        "overlap": 14,
        "keep_shoulder": 10,
        "body_rod": False,
        "source_facing": 1,
    },
}


def build(name, cfg):
    im = Image.open(ASSETS / f"{name}.png").convert("RGBA")
    im = im.crop(im.getbbox())
    a = np.array(im)
    alive = a[..., 3] > 20

    if cfg.get("poly"):
        from PIL import ImageDraw
        pm = Image.new("L", (im.width, im.height), 0)
        ImageDraw.Draw(pm).polygon([tuple(pt) for pt in cfg["poly"]], fill=255)
        arm_mask = (np.array(pm) > 0) & alive
    else:
        x0, x1, y0, y1 = cfg["cut"]
        cut = alive.copy()
        cut[y0:y1, x0:x1] = False
        lab, _ = ndi.label(cut)
        px, py = cfg["probe"]
        k = lab[py, px]
        if k == 0:
            raise SystemExit(f"[{name}] titik probe {cfg['probe']} tidak kena lengan")
        arm_mask = lab == k
    # tutup lubang kecil agar tepi lengan halus
    arm_mask = ndi.binary_dilation(arm_mask, iterations=2) & alive

    keep = np.zeros_like(arm_mask)
    r = cfg.get("keep_shoulder", 0)
    if r:
        yy0, xx0 = np.mgrid[0:arm_mask.shape[0], 0:arm_mask.shape[1]]
        keep = (xx0 - cfg["shoulder"][0]) ** 2 + (yy0 - cfg["shoulder"][1]) ** 2 <= r * r
    body = a.copy(); body[arm_mask & ~keep] = 0
    if cfg.get("erase"):
        from PIL import ImageDraw
        em = Image.new("L", (im.width, im.height), 0)
        for poly in cfg["erase"]:
            ImageDraw.Draw(em).polygon([tuple(pt) for pt in poly], fill=255)
        body[(np.array(em) > 0) & ~arm_mask] = 0
    arm = a.copy(); arm[~arm_mask] = 0

    ys, xs = np.where(arm_mask)
    ax0, ay0, ax1, ay1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1

    ov = cfg["overlap"]
    if cfg.get("split_y") is not None:
        sy = cfg["split_y"]
        upper = arm.copy(); upper[sy + ov:, :, :] = 0
        fore = arm.copy(); fore[: sy - ov, :, :] = 0
    else:
        u = np.array(cfg["elbow"], float) - np.array(cfg["shoulder"], float)
        u /= np.linalg.norm(u)
        yy_, xx_ = np.mgrid[0:arm.shape[0], 0:arm.shape[1]]
        t = (xx_ - cfg["elbow"][0]) * u[0] + (yy_ - cfg["elbow"][1]) * u[1]
        upper = arm.copy(); upper[t > ov] = 0
        fore = arm.copy(); fore[t < -ov] = 0

    def crop_to(img, ref_xy):
        al = img[..., 3] > 0
        yy, xx = np.where(al)
        bx0, by0, bx1, by1 = xx.min(), yy.min(), xx.max() + 1, yy.max() + 1
        piece = Image.fromarray(img[by0:by1, bx0:bx1])
        return piece, (ref_xy[0] - bx0, ref_xy[1] - by0), (bx0, by0)

    out = ASSETS / "rig" / name
    out.mkdir(parents=True, exist_ok=True)

    body_img = Image.fromarray(body)
    body_img.save(out / "body.png")
    up_img, up_sh, up_off = crop_to(upper, cfg["shoulder"])
    up_img.save(out / "upper.png")
    fo_img, fo_el, fo_off = crop_to(fore, cfg["elbow"])
    fo_img.save(out / "fore.png")

    sh, el, hd = map(np.array, (cfg["shoulder"], cfg["elbow"], cfg["hand"]))
    rig = {
        "source_facing": cfg["source_facing"],
        "body_size": list(body_img.size),
        "shoulder_on_body": list(cfg["shoulder"]),
        "upper": {"file": "upper.png", "pivot": [float(up_sh[0]), float(up_sh[1])],
                  "elbow_local": [float(cfg["elbow"][0] - up_off[0]), float(cfg["elbow"][1] - up_off[1])]},
        "fore": {"file": "fore.png", "pivot": [float(fo_el[0]), float(fo_el[1])],
                 "hand_local": [float(cfg["hand"][0] - fo_off[0]), float(cfg["hand"][1] - fo_off[1])]},
        "len_upper": float(np.linalg.norm(el - sh)),
        "len_fore": float(np.linalg.norm(hd - el)),
        "rest_upper_angle": float(np.degrees(np.arctan2(*(el - sh)[::-1]))),
        "rest_fore_angle": float(np.degrees(np.arctan2(*(hd - el)[::-1]))),
        "hip_on_body": [int(body_img.width * 0.5), int(body_img.height * 0.62)],
    }
    if cfg.get("rod_anchor"):
        rig["rod_anchor"] = list(cfg["rod_anchor"])
    if cfg.get("body_rod") is False:
        rig["body_rod"] = False
    (out / "rig.json").write_text(json.dumps(rig, indent=2), encoding="utf-8")
    print(f"[OK] {name}: {out}")
    print(json.dumps(rig, indent=2))


if __name__ == "__main__":
    names = sys.argv[1:] or list(RIGS)
    for n in names:
        build(n, RIGS[n])
