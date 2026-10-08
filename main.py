import argparse
import json
import math
import re
import time
import traceback
from pathlib import Path

import cv2
import numpy as np
import pygame
from pygame.math import Vector2

from rigmath import solve_arm, arm_target_from_hand

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
AUDIO = ROOT / "audio"
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
STORY = json.loads((ROOT / "story.json").read_text(encoding="utf-8"))

BG_FILES = {
    # Background khusus antarmuka utama, Quiz, dan Gesture Attack.
    # Story tetap memakai background ceritanya sendiri.
    "ui_edalang": "bg_edalang_ui.jpg",
    # Background batik krem untuk Menu Utama dan Gesture Attack (Quiz tetap memakai ui_edalang).
    "ui_batik": "bg_batik_ui.jpg",
    # Background mode Story sesuai empat foto yang dikirim pengguna.
    "hutan_sore": "story_hutan.jpg",
    "persimpangan": "story_persimpangan.jpg",
    "jejak_kaki": "story_jejak.jpg",
    "keluar_hutan": "story_keluar.jpg",
}

# Teks pembukaan HARUS sama persis dengan rekaman 01_pembukaan.mp3.
# Jangan memakai teks narasi adegan 1 di bagian pembukaan karena audionya berbeda.
OPENING_PAGES = [
    "Di sebuah hutan yang jauh dari keramaian, dua kesatria sedang menempuh perjalanan panjang.",
    "Bima dan Arjuna berjalan bersama, melewati pepohonan yang lebat dan jalan setapak yang sunyi.",
    "Namun, perjalanan mereka tidak selalu berjalan mudah. Di tengah hutan, mereka harus menghadapi sebuah pilihan yang menguji kesabaran, keyakinan, dan hubungan di antara mereka.",
    "Akankah mereka mampu menemukan jalan yang benar?",
    "Dan mampukah mereka tetap saling percaya, meskipun memiliki pendapat yang berbeda?",
]

# Batas subtitle pembukaan berdasarkan jeda suara 01_pembukaan.mp3.
# Angka ini mencegah subtitle tertinggal karena pembagian hanya berdasarkan jumlah kata.
OPENING_TIMINGS = [
    (0.00, 6.54),
    (6.54, 14.16),
    (14.16, 21.98),
    (21.98, 27.45),
    (27.45, 33.64),
]

# Timestamp subtitle narasi berdasarkan jeda aktual tiap rekaman.
# Subtitle mulai dari awal suara supaya tidak terasa terlambat.
NARRATION_TIMINGS = {
    "07_adegan1.mp3": [(0.00, 6.05), (6.05, 11.55)],
    "08_adegan2.mp3": [(0.00, 4.79), (4.79, 8.69), (8.69, 13.53), (13.53, 17.21)],
    "09_adegan3.mp3": [(0.00, 5.10), (5.10, 9.61), (9.61, 15.15), (15.15, 20.19)],
    "10_adegan4.mp3": [(0.00, 5.89), (5.89, 11.00), (11.00, 14.79), (14.79, 22.81), (22.81, 29.52)],
    "11_adegan5.mp3": [(0.00, 7.11), (7.11, 14.45), (14.45, 22.77), (22.77, 34.27)],
    "12_akhir_cerita.mp3": [(0.00, 7.11), (7.11, 14.45), (14.45, 22.77), (22.77, 34.27)],
    "13_pesan_moral.mp3": [(0.00, 5.61), (5.61, 10.38), (10.38, 15.88)],
    "14_penutup.mp3": [(0.00, 4.69), (4.69, 7.59), (7.59, 12.38)],
}
AFTER_PAUSE_TEXT = "Kisah ini membawa kita pada sebuah perjalanan sederhana, tetapi menyimpan pelajaran tentang persahabatan dan kebersamaan."
FINAL_STORY_TEXT = (
    "Bima dan Arjuna akhirnya melanjutkan perjalanan melalui jalan yang telah mereka pilih bersama. "
    "Dari perjalanan tersebut, mereka belajar bahwa perbedaan pendapat bukanlah alasan untuk bertengkar. "
    "Dengan keberanian, kebijaksanaan, dan kerja sama, mereka dapat menghadapi berbagai kesulitan. "
    "Bima dan Arjuna kemudian melanjutkan perjalanan dengan hati yang tenang, sambil menjaga janji untuk selalu saling menghargai dan membantu."
)
MORAL_TEXT = (
    "Dari kisah Bima dan Arjuna, kita belajar bahwa perbedaan pendapat bukanlah alasan untuk saling bermusuhan. "
    "Dengan saling mendengarkan, menghargai, dan bekerja sama, setiap masalah dapat dihadapi dengan lebih baik."
)
CLOSING_TEXT = (
    "Demikianlah kisah perjalanan Bima dan Arjuna. Semoga kisah ini mengingatkan kita untuk selalu menjaga persahabatan dan menghargai satu sama lain."
)
ENDING_TEXT = "Perbedaan bukanlah penghalang untuk tetap bersama."

QUIZ_QUESTIONS = [
    {
        "question": "Mengapa Bima dan Arjuna berhenti di persimpangan?",
        "options": ["Mencari makanan", "Menentukan jalan yang benar", "Mencari rumah", "Menunggu hujan"],
        "answer": 1,
        "explanation": "Mereka berhenti karena harus menentukan jalan yang tepat untuk melanjutkan perjalanan.",
    },
    {
        "question": "Jalan mana yang awalnya dipilih Bima?",
        "options": ["Jalan kanan", "Jalan tengah", "Jalan kiri", "Jalan belakang"],
        "answer": 2,
        "explanation": "Bima awalnya memilih jalan kiri sebelum mereka mencari petunjuk lebih lanjut.",
    },
    {
        "question": "Apa yang dilakukan Bima dan Arjuna untuk menentukan jalan?",
        "options": ["Bertengkar", "Mencari petunjuk bersama", "Berpisah", "Menunggu orang lain"],
        "answer": 1,
        "explanation": "Keduanya mencari petunjuk bersama agar dapat menentukan arah perjalanan dengan bijak.",
    },
    {
        "question": "Petunjuk apa yang mereka temukan?",
        "options": ["Peta", "Jejak kaki", "Kompas", "Jembatan"],
        "answer": 1,
        "explanation": "Jejak kaki menjadi petunjuk yang membantu mereka memilih arah di persimpangan.",
    },
    {
        "question": "Apa pesan utama dari kisah Bima dan Arjuna?",
        "options": ["Selalu mengikuti pendapat sendiri", "Perbedaan harus dihindari", "Saling menghargai dan bekerja sama", "Jangan bepergian ke hutan"],
        "answer": 2,
        "explanation": "Kisah ini menekankan pentingnya saling menghargai, bekerja sama, dan mengambil keputusan bersama.",
    },
]


def safe_sound_file(name):
    p = AUDIO / name
    return p if p.exists() else None


def validate_story_assets():
    """Validate the complete story before the first frame is shown.

    This prevents a missing asset from silently shortening the story and
    makes the terminal show exactly what will be played.
    """
    errors = []

    if not STORY.get("scenes"):
        errors.append("story.json tidak memiliki scenes.")

    for scene in STORY.get("scenes", []):
        sid = scene.get("id", "?")
        narration = scene.get("narration")
        if not narration or safe_sound_file(narration) is None:
            errors.append(f"Adegan {sid}: audio narasi tidak ditemukan: {narration}")

        dialogues = scene.get("dialogues", [])
        for idx, item in enumerate(dialogues, 1):
            if not isinstance(item, (list, tuple)) or len(item) != 3:
                errors.append(f"Adegan {sid} dialog {idx}: format harus [speaker, text, audio].")
                continue
            speaker, text, audio_name = item
            if not str(speaker).strip() or not str(text).strip():
                errors.append(f"Adegan {sid} dialog {idx}: speaker/teks kosong.")
            if safe_sound_file(audio_name) is None:
                errors.append(f"Adegan {sid} dialog {idx}: audio tidak ditemukan: {audio_name}")

        if scene.get("background") not in BG_FILES:
            errors.append(f"Adegan {sid}: background tidak dikenal: {scene.get('background')}")

    intro_audio = [
        "01_pembukaan.mp3", "02_setelah_jeda.mp3", "04_mari_kita_ikuti.mp3",
        "05_judul_subjudul.mp3", "06_judul_utama.mp3",
        "12_akhir_cerita.mp3", "13_pesan_moral.mp3", "14_penutup.mp3",
    ]
    for name in intro_audio:
        if safe_sound_file(name) is None:
            errors.append(f"Audio utama tidak ditemukan: {name}")

    if errors:
        print("\n[ERROR] Validasi aset gagal:")
        for err in errors:
            print("  -", err)
        raise RuntimeError("Ada aset/format cerita yang tidak valid. Perbaiki daftar di atas.")

    print("[CHECK] Semua audio, dialog, dan background ditemukan.")
    print("[CHECK] Urutan cerita:")
    for scene in STORY["scenes"]:
        print(f"  Adegan {scene['id']}: narasi -> {len(scene['dialogues'])} dialog")


class Puppet:
    def __init__(self, filename, x, y, target_height, ox, oy):
        path = ASSETS / filename
        if not path.exists():
            raise FileNotFoundError(f"File wayang tidak ditemukan: {path}")
        original = pygame.image.load(str(path)).convert_alpha()
        bbox = original.get_bounding_rect(min_alpha=8)
        if bbox.width > 2 and bbox.height > 2:
            original = original.subsurface(bbox).copy()
        ratio = target_height / max(1, original.get_height())
        self.base = pygame.transform.smoothscale(
            original,
            (max(1, int(original.get_width() * ratio)), max(1, int(original.get_height() * ratio))),
        )
        self.image = self.base
        self.pos = Vector2(x, y)
        self.target = self.pos.copy()
        self.offset = Vector2(ox, oy)
        # Arah hadap asli gambar sumber: +1 = menghadap kanan, -1 = kiri.
        self.source_facing = 1
        self.facing = 1

    def set_facing(self, direction):
        """Set arah hadap visual secara langsung (+1 kanan, -1 kiri)."""
        direction = -1 if direction < 0 else 1
        if direction != self.facing:
            self.facing = direction
            self.image = pygame.transform.flip(self.base, True, False) if direction < 0 else self.base

    def set_visual_facing(self, direction, source_facing=None):
        """Set arah visual dengan memperhitungkan orientasi asli aset."""
        direction = -1 if direction < 0 else 1
        if source_facing is not None:
            self.source_facing = -1 if source_facing < 0 else 1
        # Jika arah sumber sama dengan arah yang diinginkan, gunakan gambar asli.
        # Jika berbeda, mirror secara horizontal.
        needs_flip = self.source_facing != direction
        self.facing = direction
        self.image = pygame.transform.flip(self.base, True, False) if needs_flip else self.base

    def update(self, palm, smooth):
        if palm is not None:
            self.target = Vector2(palm) + self.offset
        self.pos += (self.target - self.pos) * smooth

    def update_hand(self, hand, smooth):
        """Wayang statis: hanya mengikuti telapak tangan."""
        self.update(hand["palm"], smooth)

    def draw(self, screen):
        rect = self.image.get_rect(center=(round(self.pos.x), round(self.pos.y)))
        try:
            mask = pygame.mask.from_surface(self.image, 8)
            halo = mask.to_surface(setcolor=(*HALO_COLORS[STYLE["halo"]], 255), unsetcolor=(0, 0, 0, 0))
            halo.set_colorkey((0, 0, 0, 0))
            for dx, dy in ((-3,0),(3,0),(0,-3),(0,3),(-2,-2),(2,-2),(-2,2),(2,2)):
                screen.blit(halo, (rect.x + dx, rect.y + dy))
        except Exception:
            pass
        screen.blit(self.image, rect)

    def draw_at(self, screen, center, scale=1.0):
        scale = max(0.05, scale)
        img = pygame.transform.smoothscale(
            self.image,
            (max(1, int(self.image.get_width() * scale)), max(1, int(self.image.get_height() * scale)),),
        )
        screen.blit(img, img.get_rect(center=(round(center[0]), round(center[1]))))


# Warna garis tepi (halo) wayang: "gold" untuk latar gelap, "dark" untuk latar krem/terang.
STYLE = {"halo": "gold"}
HALO_COLORS = {"gold": (238, 196, 105), "dark": (66, 38, 20)}


def _blit_rot(dest, img, pivot, at, ccw_deg):
    """Gambar img diputar ccw_deg (berlawanan jarum jam) mengelilingi titik pivot, pivot diletakkan di 'at'."""
    w, h = img.get_size()
    rot = pygame.transform.rotate(img, ccw_deg)
    v = Vector2(pivot[0] - w / 2, pivot[1] - h / 2).rotate(-ccw_deg)
    dest.blit(rot, rot.get_rect(center=(round(at[0] - v.x), round(at[1] - v.y))))


def _make_halo(img, pad=5, color=(238, 196, 105)):
    w, h = img.get_size()
    sil = pygame.mask.from_surface(img, 8).to_surface(setcolor=(*color, 255), unsetcolor=(0, 0, 0, 0))
    out = pygame.Surface((w + 2 * pad, h + 2 * pad), pygame.SRCALPHA)
    for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, -2), (-2, 2), (2, 2)):
        out.blit(sil, (pad + dx, pad + dy))
    return out


class RiggedPuppet:
    """Wayang berartikulasi: badan + lengan depan (atas & bawah) dengan IK.
    Badan mengikuti telapak tangan (miring/berayun), lengan mengikuti arah jari.
    Bagian-bagian dibuat oleh tools/make_rig.py ke assets/rig/<nama>/."""
    PAD = 5

    def __init__(self, filename, x, y, target_height, ox, oy):
        stem = Path(filename).stem
        rdir = ASSETS / "rig" / stem
        rig = json.loads((rdir / "rig.json").read_text(encoding="utf-8"))
        self.cfg = CONFIG.get("rig", {})
        raw = {k: pygame.image.load(str(rdir / f"{k}.png")).convert_alpha() for k in ("body", "upper", "fore")}
        s = target_height / max(1, raw["body"].get_height())
        self.s = s
        sc = lambda im: pygame.transform.smoothscale(im, (max(1, int(im.get_width() * s)), max(1, int(im.get_height() * s))))
        self.body, self.upper, self.fore = sc(raw["body"]), sc(raw["upper"]), sc(raw["fore"])
        self.halo_sets = {k: tuple(_make_halo(i, self.PAD, c) for i in (self.body, self.upper, self.fore))
                          for k, c in HALO_COLORS.items()}
        self.up_pivot = Vector2(rig["upper"]["pivot"]) * s
        self.fo_pivot = Vector2(rig["fore"]["pivot"]) * s
        self.shoulder = Vector2(rig["shoulder_on_body"]) * s
        self.lu, self.lf = rig["len_upper"] * s, rig["len_fore"] * s
        self.rest_u = math.radians(rig["rest_upper_angle"])
        self.rest_f = math.radians(rig["rest_fore_angle"])
        hand_rest = Vector2(rig["shoulder_on_body"]) + (Vector2(rig["fore"]["hand_local"]) - Vector2(rig["fore"]["pivot"])) \
            + (Vector2(rig["upper"]["elbow_local"]) - Vector2(rig["upper"]["pivot"]))
        self.rest_vec = (hand_rest - Vector2(rig["shoulder_on_body"])) * s
        self.rod_anchor = Vector2(rig.get("rod_anchor", [rig["body_size"][0] * 0.5, rig["body_size"][1] * 0.42])) * s
        self.M = int((self.lu + self.lf) * 1.08) + self.PAD + 4
        self.body_rod = bool(rig.get("body_rod", True))
        self.pos = Vector2(x, y)
        self.target = self.pos.copy()
        self.offset = Vector2(ox, oy)
        self.source_facing = int(rig.get("source_facing", -1))
        self.facing = 1
        self.flip = False
        self.arm_vec = Vector2(self.rest_vec)
        self.arm_goal = Vector2(self.rest_vec)
        self.hand_ttl = 0
        self.tilt = 0.0
        self.tilt_goal = 0.0
        self.prev_x = self.pos.x
        self.image = self.body  # kompatibilitas

    # --- arah hadap (sama dengan Puppet) ---
    def set_facing(self, direction):
        direction = -1 if direction < 0 else 1
        self.facing = direction
        self.flip = direction < 0

    def set_visual_facing(self, direction, source_facing=None):
        direction = -1 if direction < 0 else 1
        if source_facing is not None:
            self.source_facing = -1 if source_facing < 0 else 1
        self.facing = direction
        self.flip = self.source_facing != direction

    # --- input ---
    def update(self, palm, smooth):
        if palm is not None:
            self.target = Vector2(palm) + self.offset
        self.pos += (self.target - self.pos) * smooth

    def update_hand(self, hand, smooth):
        self.update(hand["palm"], smooth)
        self.hand_ttl = 10
        wrist = hand.get("wrist")
        size = hand.get("size", 0) or 0
        if wrist is None or size <= 1:
            return
        mode = self.cfg.get("arm_driver", "thumb")
        key, lo, hi = ("thumb", 0.85, 1.35) if mode == "thumb" else ("tip", 1.35, 2.0)
        pt = hand.get(key)
        if pt is None:
            return
        v = (Vector2(pt) - Vector2(wrist)) / size
        tgt = arm_target_from_hand((v.x, v.y), self.flip, self.lu, self.lf, lo, hi)
        if tgt is not None:
            self.arm_goal = Vector2(tgt)
        # kemiringan badan dari rotasi tangan (telapak tegak = 0)
        palm = Vector2(hand["palm"])
        r = palm - Vector2(wrist)
        roll = math.degrees(math.atan2(r.x, -r.y)) if r.length() > 1 else 0.0
        self.tilt_goal = max(-12.0, min(12.0, -roll * float(self.cfg.get("roll_gain", 0.35))))

    # --- gambar ---
    def _frame(self):
        cfg = self.cfg
        t = pygame.time.get_ticks() / 1000.0
        if self.hand_ttl > 0:
            self.hand_ttl -= 1
            goal = self.arm_goal
            tilt_goal = self.tilt_goal
        else:
            goal = Vector2(self.rest_vec)
            tilt_goal = 0.0
        a = float(cfg.get("arm_smooth", 0.35))
        self.arm_vec += (goal - self.arm_vec) * a
        # ayunan karena kecepatan gerak + napas pelan
        vel = self.pos.x - self.prev_x
        self.prev_x = self.pos.x
        sway = max(-8.0, min(8.0, -vel * float(cfg.get("sway_gain", 0.25))))
        self.tilt += (tilt_goal + sway - self.tilt) * 0.25
        tilt = self.tilt + math.sin(t * 1.7) * 0.8

        M = self.M
        bw, bh = self.body.get_size()
        canvas = pygame.Surface((bw + 2 * M, bh + 2 * M), pygame.SRCALPHA)
        S = self.shoulder + Vector2(M, M)
        th_u, th_f, E, Hd = solve_arm((self.arm_vec.x, self.arm_vec.y), self.lu, self.lf)
        Ep, Hp = S + Vector2(E), S + Vector2(Hd)
        du = -math.degrees(th_u - self.rest_u)
        df = -math.degrees(th_f - self.rest_f)
        P = self.PAD
        body_halo, upper_halo, fore_halo = self.halo_sets[STYLE["halo"]]
        canvas.blit(body_halo, (M - P, M - P))
        _blit_rot(canvas, fore_halo, self.fo_pivot + Vector2(P, P), Ep, df)
        _blit_rot(canvas, upper_halo, self.up_pivot + Vector2(P, P), S, du)
        canvas.blit(self.body, (M, M))
        _blit_rot(canvas, self.fore, self.fo_pivot, Ep, df)
        _blit_rot(canvas, self.upper, self.up_pivot, S, du)

        img = pygame.transform.rotate(canvas, tilt)
        if self.flip:
            img = pygame.transform.flip(img, True, False)
        center = Vector2(canvas.get_width() / 2, canvas.get_height() / 2)

        def to_screen_vec(p):
            v = (Vector2(p) - center).rotate(-tilt)
            if self.flip:
                v.x = -v.x
            return v
        return img, to_screen_vec(Hp), to_screen_vec(self.rod_anchor + Vector2(M, M))

    def _rod(self, screen, start, end, width):
        pygame.draw.line(screen, (38, 24, 16), start, end, width + 2)
        pygame.draw.line(screen, (96, 64, 38), start, end, max(1, width - 1))

    def draw(self, screen):
        img, hand_v, rod_v = self._frame()
        c = (round(self.pos.x), round(self.pos.y))
        H = screen.get_height()
        rods = bool(self.cfg.get("rods", True))
        if rods and self.body_rod:  # gapit badan di belakang wayang
            a = Vector2(c) + rod_v
            self._rod(screen, a, (a.x - 10 * (1 if not self.flip else -1), H + 20), max(4, int(self.s * 22)))
        screen.blit(img, img.get_rect(center=c))
        if rods:  # tuding/gapit tangan
            h = Vector2(c) + hand_v
            self._rod(screen, h, (h.x + (14 if not self.flip else -14), H + 20), max(3, int(self.s * 15)))

    def draw_at(self, screen, center, scale=1.0):
        scale = max(0.05, scale)
        img, _, _ = self._frame()
        img = pygame.transform.smoothscale(img, (max(1, int(img.get_width() * scale)), max(1, int(img.get_height() * scale))))
        screen.blit(img, img.get_rect(center=(round(center[0]), round(center[1]))))


def make_puppet(filename, x, y, target_height, ox, oy):
    """Pakai wayang berartikulasi jika rig tersedia, jika tidak pakai wayang statis."""
    stem = Path(filename).stem
    if CONFIG.get("rig", {}).get("enabled", True) and (ASSETS / "rig" / stem / "rig.json").exists():
        try:
            return RiggedPuppet(filename, x, y, target_height, ox, oy)
        except Exception as exc:
            print(f"[WARNING] Rig {stem} gagal dimuat ({exc}); memakai wayang statis.")
    return Puppet(filename, x, y, target_height, ox, oy)


# ---------------------------------------------------------------------------
# Tampilan responsif: semua digambar ke kanvas logis W x H (mis. 1280x720),
# lalu diskalakan ke jendela/fullscreen dengan menjaga rasio (letterbox).
# Posisi mouse dikonversi balik ke koordinat kanvas.
# ---------------------------------------------------------------------------
_VIEW = {"scale": 1.0, "ox": 0, "oy": 0}


def present_canvas(canvas):
    window = pygame.display.get_surface()
    ww, wh = window.get_size()
    cw, ch = canvas.get_size()
    sc = min(ww / cw, wh / ch)
    nw, nh = max(1, int(cw * sc)), max(1, int(ch * sc))
    ox, oy = (ww - nw) // 2, (wh - nh) // 2
    _VIEW.update(scale=sc, ox=ox, oy=oy)
    window.fill((0, 0, 0))
    if (nw, nh) == (cw, ch):
        window.blit(canvas, (ox, oy))
    else:
        window.blit(pygame.transform.smoothscale(canvas, (nw, nh)), (ox, oy))
    pygame.display.flip()


def logical_pos(pos):
    """Konversi posisi mouse jendela -> koordinat kanvas logis."""
    sc = _VIEW["scale"] or 1.0
    return (int((pos[0] - _VIEW["ox"]) / sc), int((pos[1] - _VIEW["oy"]) / sc))


def logical_mouse():
    return logical_pos(pygame.mouse.get_pos())


def load_backgrounds(size):
    W, H = size
    result = {}
    for key, filename in BG_FILES.items():
        path = ASSETS / filename
        if not path.exists():
            print(f"[WARNING] Background tidak ditemukan: {path}")
            continue
        img = pygame.image.load(str(path)).convert()
        iw, ih = img.get_size()
        scale = max(W / iw, H / ih)
        nw, nh = max(W, int(iw * scale)), max(H, int(ih * scale))
        img = pygame.transform.smoothscale(img, (nw, nh))
        x = (nw - W) // 2
        y = (nh - H) // 2
        result[key] = img.subsurface(pygame.Rect(x, y, W, H)).copy()
    return result


def draw_background(screen, backgrounds, key, W, H):
    bg = backgrounds.get(key)
    if bg is None:
        screen.fill((25, 25, 25))
    else:
        screen.blit(bg, (0, 0))


def gesture_state(hand):
    lm = hand.landmark
    wrist = np.array([lm[0].x, lm[0].y], np.float32)
    palm_points = np.array([[lm[i].x, lm[i].y] for i in (5, 9, 13, 17)], np.float32)
    palm_size = max(float(np.mean(np.linalg.norm(palm_points - wrist, axis=1))), 1e-4)
    pairs = [(8, 6), (12, 10), (16, 14), (20, 18)]
    extended = 0
    folded = 0
    for tip, pip in pairs:
        dt = np.linalg.norm(np.array([lm[tip].x, lm[tip].y]) - wrist) / palm_size
        dp = np.linalg.norm(np.array([lm[pip].x, lm[pip].y]) - wrist) / palm_size
        if dt > dp * 1.12 and dt > 1.25:
            extended += 1
        elif dt < dp * 1.05:
            folded += 1
    if extended >= 4:
        return 1
    if folded >= 4:
        return -1
    return 0


class GestureStabilizer:
    def __init__(self, required_frames=6):
        self.required_frames = required_frames
        self.candidate = 0
        self.count = 0
        self.stable = 1

    def update(self, state):
        if state == 0:
            self.candidate = 0
            self.count = 0
            return self.stable
        if state == self.stable:
            self.candidate = 0
            self.count = 0
            return self.stable
        if state == self.candidate:
            self.count += 1
        else:
            self.candidate = state
            self.count = 1
        if self.count >= self.required_frames:
            self.stable = state
            self.candidate = 0
            self.count = 0
        return self.stable


def _hand_info(hand, W, H):
    lm = hand.landmark
    pt = lambda i: Vector2(lm[i].x * W, lm[i].y * H)
    wrist, palm = pt(0), pt(9)
    return {
        "palm": palm,
        "gesture": gesture_state(hand),
        "wrist": wrist,
        "tip": pt(8),
        "thumb": pt(4),
        "size": max(wrist.distance_to(palm), 1.0),
    }


def detect_hands(result, W, H):
    found = {}
    if not result.multi_hand_landmarks:
        return found
    infos = [_hand_info(h, W, H) for h in result.multi_hand_landmarks]
    for i, info in enumerate(infos):
        label = None
        if result.multi_handedness and i < len(result.multi_handedness):
            label = result.multi_handedness[i].classification[0].label
        if label:
            found[label] = info
    if not found:
        infos = sorted(infos, key=lambda x: x["palm"].x)
        if len(infos) == 1:
            found["Unknown"] = infos[0]
        elif len(infos) >= 2:
            found["Right"] = infos[0]
            found["Left"] = infos[-1]
    return found


def make_camera_preview(frame, result=None, preview_size=(430, 322)):
    """Create a mirrored live-camera preview with optional MediaPipe landmarks."""
    if frame is None:
        return None
    try:
        preview = frame.copy()
        if result is not None and getattr(result, "multi_hand_landmarks", None):
            h, w = preview.shape[:2]
            connections = [
                (0,1),(1,2),(2,3),(3,4),
                (0,5),(5,6),(6,7),(7,8),
                (5,9),(9,10),(10,11),(11,12),
                (9,13),(13,14),(14,15),(15,16),
                (13,17),(17,18),(18,19),(19,20),(0,17)
            ]
            for hand in result.multi_hand_landmarks:
                pts = []
                for lm in hand.landmark:
                    pts.append((int(lm.x * w), int(lm.y * h)))
                for a, b in connections:
                    cv2.line(preview, pts[a], pts[b], (50, 235, 80), 2, cv2.LINE_AA)
                for x, y in pts:
                    cv2.circle(preview, (x, y), 4, (35, 255, 90), -1, cv2.LINE_AA)
                    cv2.circle(preview, (x, y), 5, (15, 55, 20), 1, cv2.LINE_AA)
        target_w, target_h = preview_size
        preview = cv2.resize(preview, (target_w, target_h), interpolation=cv2.INTER_AREA)
        rgb = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
        return pygame.image.frombuffer(rgb.tobytes(), (target_w, target_h), "RGB").convert()
    except Exception:
        return None



def make_camera_cv_preview(frame, result=None, target_size=(480, 360)):
    """Build the live POV as an OpenCV frame for a separate desktop window."""
    if frame is None:
        return None
    try:
        preview = frame.copy()
        if result is not None and getattr(result, "multi_hand_landmarks", None):
            h, w = preview.shape[:2]
            connections = [
                (0,1),(1,2),(2,3),(3,4),
                (0,5),(5,6),(6,7),(7,8),
                (5,9),(9,10),(10,11),(11,12),
                (9,13),(13,14),(14,15),(15,16),
                (13,17),(17,18),(18,19),(19,20),(0,17)
            ]
            for hand in result.multi_hand_landmarks:
                pts = [(int(lm.x*w), int(lm.y*h)) for lm in hand.landmark]
                for a,b in connections:
                    cv2.line(preview, pts[a], pts[b], (50,235,80), 2, cv2.LINE_AA)
                for x,y in pts:
                    cv2.circle(preview, (x,y), 4, (35,255,90), -1, cv2.LINE_AA)
                    cv2.circle(preview, (x,y), 5, (15,55,20), 1, cv2.LINE_AA)
        tw, th = target_size
        preview = cv2.resize(preview, (tw, th), interpolation=cv2.INTER_AREA)
        cv2.rectangle(preview, (0,0), (tw-1,th-1), (245,215,150), 3)
        cv2.rectangle(preview, (10,10), (230,48), (0,0,0), -1)
        cv2.putText(preview, "POV TANGAN - LIVE", (20,37),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.72, (255,245,210), 2, cv2.LINE_AA)
        cv2.rectangle(preview, (10, th-45), (tw-10, th-10), (0,0,0), -1)
        cv2.putText(preview, "Gerakkan tangan untuk mengendalikan wayang", (20, th-22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255,255,255), 1, cv2.LINE_AA)
        return preview
    except Exception:
        return None


def update_pov_window(frame, result, enabled):
    """Show POV in a separate desktop window so it never covers the story."""
    window_name = "POV Tangan - Live"
    if not enabled:
        try:
            cv2.destroyWindow(window_name)
        except Exception:
            pass
        return
    preview = make_camera_cv_preview(frame, result)
    if preview is None:
        return
    try:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 480, 360)
        cv2.imshow(window_name, preview)
        # Process the OpenCV window without waiting for input.
        cv2.waitKey(1)
    except Exception as exc:
        print(f"[WARNING] Jendela POV tidak dapat ditampilkan: {exc}")

def draw_pov_overlay(screen, camera_surface, W, H, pov_font, show_landmarks=True):
    """Draw a live POV/camera window without disturbing the story layer."""
    if camera_surface is None:
        return
    pw, ph = camera_surface.get_size()
    margin = 22
    x = W - pw - margin
    y = margin + 42

    # Shadow/backplate
    shadow = pygame.Surface((pw + 12, ph + 12), pygame.SRCALPHA)
    shadow.fill((0, 0, 0, 150))
    screen.blit(shadow, (x - 6, y - 6))

    # Camera image
    screen.blit(camera_surface, (x, y))

    # Border and title
    pygame.draw.rect(screen, (245, 215, 150), pygame.Rect(x, y, pw, ph), 3)
    label = pov_font.render("POV TANGAN • LIVE", True, (255, 245, 210))
    label_bg = pygame.Surface((label.get_width() + 18, label.get_height() + 8), pygame.SRCALPHA)
    label_bg.fill((0, 0, 0, 185))
    screen.blit(label_bg, (x + 8, y + 8))
    screen.blit(label, (x + 17, y + 12))

    info = "Gerakkan tangan untuk mengendalikan wayang"
    info_s = pygame.font.SysFont("Arial", 16).render(info, True, (255, 255, 255))
    info_bg = pygame.Surface((info_s.get_width() + 14, info_s.get_height() + 6), pygame.SRCALPHA)
    info_bg.fill((0, 0, 0, 160))
    screen.blit(info_bg, (x + 8, y + ph - info_s.get_height() - 12))
    screen.blit(info_s, (x + 15, y + ph - info_s.get_height() - 9))


class Audio:
    """Single authoritative voice channel.

    A story item is considered finished only after the actual Sound duration
    has elapsed AND the mixer channel is no longer busy. This prevents the
    next item from starting early or two voices from overlapping.
    """
    def __init__(self):
        self.channel = pygame.mixer.Channel(0)
        self.cache = {}
        self.current = None
        self.current_started = 0.0
        self.current_length = 0.0
        self.failed = False
        # Estimated speech window inside the audio. Many generated voices
        # contain a short silence at the beginning/end; using the full MP3
        # length makes subtitles visibly lag behind the spoken words.
        self.current_lead = 0.0
        self.current_tail = 0.0
        self.timings = {}

    def sound(self, filename):
        if filename not in self.cache:
            path = safe_sound_file(filename)
            if path is None:
                print(f"[ERROR] Audio tidak ditemukan: {filename}")
                return None
            try:
                sound = pygame.mixer.Sound(str(path))
                self.cache[filename] = sound
                self.timings[filename] = self._estimate_speech_window(sound)
            except Exception as exc:
                print(f"[ERROR] Gagal memuat audio {filename}: {exc}")
                return None
        return self.cache[filename]

    def _estimate_speech_window(self, sound):
        """Estimate non-silent speech bounds from the decoded Sound.

        This is deliberately conservative: it removes only obvious leading
        and trailing silence, so subtitles follow speech rather than the
        encoder padding of an MP3.
        """
        try:
            arr = pygame.sndarray.array(sound)
            if arr is None or arr.size == 0:
                return 0.0, 0.0
            a = np.asarray(arr)
            if a.ndim > 1:
                a = np.max(np.abs(a.astype(np.float32)), axis=1)
            else:
                a = np.abs(a.astype(np.float32))
            peak = float(np.max(a))
            if peak <= 1e-6:
                return 0.0, 0.0
            # About -34 dB from peak; enough to ignore encoder silence while
            # preserving soft consonants in normal generated speech.
            threshold = peak * 0.02
            active = np.flatnonzero(a > threshold)
            if active.size == 0:
                return 0.0, 0.0
            # sndarray's first axis is already the sample/time axis, even
            # for stereo arrays, so no channel division is needed here.
            freq = max(1, int(pygame.mixer.get_init()[0]))
            first = float(active[0]) / freq
            last = float(active[-1] + 1) / freq
            length = float(sound.get_length())
            # Clamp: never remove more than 0.35 s from either side.
            lead = max(0.0, min(0.35, first))
            tail = max(0.0, min(0.45, length - last))
            return lead, tail
        except Exception:
            return 0.0, 0.0

    def preload_all(self):
        """Load every story voice before the first frame is played.

        Loading an MP3 for the first time during a transition can introduce a
        small stall. Preloading removes that source of timing jitter and makes
        every story item start from the same state.
        """
        names = [
            "01_pembukaan.mp3", "02_setelah_jeda.mp3", "04_mari_kita_ikuti.mp3",
            "05_judul_subjudul.mp3", "06_judul_utama.mp3",
            "12_akhir_cerita.mp3", "13_pesan_moral.mp3", "14_penutup.mp3",
        ]
        for scene in STORY.get("scenes", []):
            names.append(scene.get("narration"))
            for item in scene.get("dialogues", []):
                if isinstance(item, (list, tuple)) and len(item) == 3:
                    names.append(item[2])
        names = [n for n in names if n]
        for name in dict.fromkeys(names):
            sound = self.sound(name)
            if sound is None:
                raise RuntimeError(f"Audio gagal dipersiapkan: {name}")
        print(f"[CHECK] {len(dict.fromkeys(names))} file voice berhasil dipreload ke memori.")

    def play(self, filename):
        sound = self.sound(filename)
        self.channel.stop()
        self.current = filename
        self.current_length = float(sound.get_length()) if sound else 0.0
        self.failed = sound is None
        if sound is not None:
            self.channel.play(sound)
            # Timestamp and speech bounds belong to the same playback event.
            self.current_started = time.monotonic()
            self.current_lead, self.current_tail = self.timings.get(filename, (0.0, 0.0))
            print(f"[AUDIO] Mulai: {filename} ({self.current_length:.2f}s, lead={self.current_lead:.2f}s, tail={self.current_tail:.2f}s)")
            return True
        self.current_started = time.monotonic()
        return False

    def busy(self):
        if self.current is None:
            return False
        if self.failed:
            return False
        elapsed = time.monotonic() - self.current_started
        # Keep a tiny safety tail so the next voice cannot cut off the last
        # syllable because of mixer scheduling.
        return elapsed < self.current_length or self.channel.get_busy()

    def done(self, safety=0.12):
        if self.current is None:
            return True
        if self.failed:
            return True
        elapsed = time.monotonic() - self.current_started
        return elapsed >= self.current_length + safety and not self.channel.get_busy()

    def elapsed(self):
        return max(0.0, time.monotonic() - self.current_started)

    def progress(self):
        if self.current_length <= 0:
            return 1.0
        return max(0.0, min(1.0, self.elapsed() / self.current_length))

    def stop(self):
        self.channel.stop()
        self.current = None
        self.current_length = 0.0
        self.failed = False
        self.current_lead = 0.0
        self.current_tail = 0.0


class Flow:
    def __init__(self):
        self.phase = "menu"
        self.phase_started = time.monotonic()
        self.played = False
        self.scene_index = 0
        self.dialog_index = 0
        self.music_started = False
        self.menu_music_started = False
        self.title_started = 0.0
        self.opening_page = 0
        self.quiz_index = 0
        self.quiz_score = 0
        self.quiz_selected = None
        self.quiz_feedback_until = 0.0
        self.quiz_finished = False
        self.char_left_idx = 2  # Bima
        self.char_right_idx = 1 # Arjuna
        self.character_slot = 0
        self.menu_hover = None
        self.settings_show_pov = True
        self.settings_music = True

    def enter(self, phase):
        self.phase = phase
        self.phase_started = time.monotonic()
        self.played = False

    def elapsed(self):
        return time.monotonic() - self.phase_started


def wrap_text(font, text, max_width):
    lines = []
    current = ""
    for word in text.split():
        trial = (current + " " + word).strip()
        if font.size(trial)[0] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def split_sentences(text):
    parts = [p.strip() for p in re.split(r'(?<=[.!?])\s+', (text or "").strip()) if p.strip()]
    return parts or ([text.strip()] if text and text.strip() else [])


def _speech_window(total_duration, lead=0.0, tail=0.0):
    total_duration = max(0.1, float(total_duration))
    lead = max(0.0, min(float(lead), total_duration * 0.25))
    tail = max(0.0, min(float(tail), total_duration * 0.25))
    start = min(lead, total_duration * 0.35)
    end = max(start + 0.15, total_duration - tail)
    if end > total_duration:
        end = total_duration
    return start, end


def _sentence_schedule(text, duration, lead=0.0, tail=0.0):
    """Return sentence timing slots weighted by word count.

    Narration is much easier to follow when one complete sentence is visible
    at a time. The previous build revealed every word across the entire
    paragraph, which made the text visibly trail the narrator. This schedule
    keeps sentence changes aligned to the voice while showing each sentence
    immediately when its spoken portion starts.
    """
    sentences = split_sentences(text)
    if not sentences:
        return []
    start, end = _speech_window(duration, lead, tail)
    usable = max(0.2, end - start)
    weights = [max(1, len(re.findall(r"\S+", x))) for x in sentences]
    total = float(sum(weights))
    slots = []
    cursor = start
    for i, (sentence, weight) in enumerate(zip(sentences, weights)):
        if i == len(sentences) - 1:
            nxt = end
        else:
            nxt = cursor + usable * (weight / total)
        slots.append((sentence, cursor, max(cursor + 0.15, nxt)))
        cursor = nxt
    return slots


def narration_sentence_state(text, elapsed, total_duration, lead=0.0, tail=0.0, timings=None):
    sentences = split_sentences(text)
    if not sentences:
        return "", 0, 0.0

    if timings and len(timings) == len(sentences):
        # NARRATION_TIMINGS stores (start, end) pairs. Older builds expected
        # (sentence, start, end), which caused:
        #   ValueError: not enough values to unpack (expected 3, got 2)
        # Normalize both formats here so a bad timing table can never crash
        # the story playback.
        normalized = []
        for i, slot in enumerate(timings):
            try:
                if len(slot) == 2:
                    a, b = float(slot[0]), float(slot[1])
                    normalized.append((sentences[i], a, b))
                elif len(slot) == 3:
                    _, a, b = slot
                    normalized.append((sentences[i], float(a), float(b)))
                else:
                    raise ValueError
            except (TypeError, ValueError, IndexError):
                normalized = []
                break
        slots = normalized if len(normalized) == len(sentences) else None
    else:
        slots = None

    if not slots:
        # Fallback: jangan menunggu lead silence. Teks harus muncul saat
        # audio mulai diputar, lalu dibagi berdasarkan bobot kata.
        start = 0.0
        end = max(0.1, float(total_duration))
        usable = end - start
        weights = [max(1, len(re.findall(r"\S+", x))) for x in sentences]
        total = float(sum(weights))
        slots = []
        cursor = start
        for i, (sentence, weight) in enumerate(zip(sentences, weights)):
            nxt = end if i == len(sentences) - 1 else cursor + usable * (weight / total)
            slots.append((sentence, cursor, max(cursor + 0.15, nxt)))
            cursor = nxt

    t = max(0.0, float(elapsed))
    idx = len(slots) - 1
    # Keep the current sentence on screen for a short safety hold at each
    # manually supplied boundary. This prevents subtitles from moving to the
    # next sentence while the narrator is still finishing the previous one.
    boundary_hold = 0.22
    for i, (_, a, b) in enumerate(slots):
        switch_at = b + (boundary_hold if i < len(slots) - 1 else 0.0)
        if t < switch_at:
            idx = i
            break
    sentence, a, b = slots[idx]
    # Fade sangat singkat agar perpindahan halus tetapi tidak terasa terlambat.
    fade = 0.05
    local = max(0.0, t - a)
    alpha = int(min(255, 255 * local / fade)) if local < fade else 255
    return sentence, alpha, float(idx)


def draw_narration(screen, text, W, H, text_font, elapsed=0.0, total_duration=1.0,
                   title="Narator", lead=0.0, tail=0.0, timings=None):
    if not text:
        return
    visible_text, alpha, _ = narration_sentence_state(
        text, elapsed, total_duration, lead, tail, timings
    )
    if not visible_text:
        return

    panel_h = 190
    panel = pygame.Surface((W - 100, panel_h), pygame.SRCALPHA)
    panel_alpha = int(190 * max(0.82, alpha / 255))
    panel.fill((0, 0, 0, panel_alpha))
    screen.blit(panel, (50, H - panel_h - 25))

    label = pygame.font.SysFont("Arial", 28, bold=True).render(
        title, True, (255, 235, 170)
    )
    label.set_alpha(alpha)
    screen.blit(label, (80, H - panel_h - 8))

    y = H - panel_h + 36
    for line in wrap_text(text_font, visible_text, W - 160)[:4]:
        surf = text_font.render(line, True, (255, 255, 255))
        surf.set_alpha(alpha)
        screen.blit(surf, (80, y))
        y += 32


def dialogue_state(text, elapsed, lead=0.0, tail=0.0):
    """Display the complete dialogue smoothly without typewriter lag.

    The voice is the timing authority. Showing the whole sentence at the
    beginning avoids the old problem where the subtitle was still revealing
    characters while the speaker had already finished the sentence.
    """
    if not text:
        return "", 0
    # Tiny fade only; do not delay the subtitle behind the voice.
    local = max(0.0, float(elapsed) - max(0.0, float(lead)))
    fade = 0.08
    alpha = 255 if local >= fade else int(max(0.0, local / fade) * 255)
    return text, alpha


def draw_dialogue(screen, speaker, text, W, H, speaker_font, text_font,
                  elapsed=0.0, total_duration=1.0, lead=0.0, tail=0.0):
    panel_h = 155
    panel = pygame.Surface((W - 80, panel_h), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 190))
    screen.blit(panel, (40, H - panel_h - 24))
    speaker_surf = speaker_font.render(speaker, True, (255, 235, 170))
    screen.blit(speaker_surf, (65, H - panel_h - 5))
    visible_text, alpha = dialogue_state(text, elapsed)
    y = H - panel_h + 32
    for line in wrap_text(text_font, visible_text, W - 150)[:3]:
        surf = text_font.render(line, True, (255, 255, 255))
        surf.set_alpha(alpha)
        screen.blit(surf, (65, y))
        y += 30


def fade_overlay(screen, W, H, alpha):
    if alpha <= 0:
        return
    overlay = pygame.Surface((W, H))
    overlay.fill((0, 0, 0))
    overlay.set_alpha(int(max(0, min(255, alpha))))
    screen.blit(overlay, (0, 0))


def draw_title(screen, W, H, big_font, sub_font, progress):
    # progress 0..1: title gently appears while the image is fading darker.
    p = max(0.0, min(1.0, progress))
    alpha = int(255 * min(1.0, p * 1.35))
    scale = 0.88 + 0.12 * min(1.0, p * 1.15)
    title = big_font.render("BIMA DAN ARJUNA", True, (255, 245, 210))
    subtitle = sub_font.render("JANJI DI TENGAH HUTAN", True, (255, 245, 210))
    if scale != 1.0:
        title = pygame.transform.smoothscale(title, (int(title.get_width()*scale), int(title.get_height()*scale)))
        subtitle = pygame.transform.smoothscale(subtitle, (int(subtitle.get_width()*scale), int(subtitle.get_height()*scale)))
    title.set_alpha(alpha)
    subtitle.set_alpha(alpha)
    screen.blit(title, title.get_rect(center=(W//2, H//2 - 35)))
    screen.blit(subtitle, subtitle.get_rect(center=(W//2, H//2 + 38)))



# ---------------------------------------------------------------------------
# MENU / MODE SYSTEM
# ---------------------------------------------------------------------------
CHARACTERS = [
    # source_facing menunjukkan arah hadap asli file gambar.
    # Gesture Attack akan otomatis membuat karakter kiri menghadap kanan
    # dan karakter kanan menghadap kiri, tanpa menganggap semua aset sama.
    {"name": "WERKUDARA", "file": "werkudara_new.png", "desc": "Kuat, berani, dan tegas", "source_facing": -1},
    {"name": "ARJUNA", "file": "arjuna_new.png", "desc": "Bijaksana, sabar, dan adil", "source_facing": -1},
    {"name": "BIMA", "file": "bima_new.png", "desc": "Pemberani, pantang menyerah", "source_facing": -1},
    {"name": "SEMAR", "file": "semar.png", "desc": "Bijaksana, sabar, rendah hati, dan setia", "source_facing": -1},
    {"name": "KAPI ANGENI", "file": "kapi_angeni.png", "desc": "Berani, tangguh, bersemangat, dan pantang mundur", "source_facing": 1},
]


def draw_gold_panel(screen, rect, title=None, subtitle=None, selected=False):
    x, y, w, h = rect
    shadow = pygame.Surface((w + 10, h + 10), pygame.SRCALPHA)
    shadow.fill((0, 0, 0, 115))
    screen.blit(shadow, (x + 5, y + 7))
    panel = pygame.Surface((w, h), pygame.SRCALPHA)
    panel.fill((35, 24, 16, 235))
    screen.blit(panel, (x, y))
    pygame.draw.rect(screen, (238, 181, 70) if selected else (154, 105, 39), pygame.Rect(x, y, w, h), 3, border_radius=10)
    pygame.draw.rect(screen, (75, 50, 26), pygame.Rect(x + 8, y + 8, w - 16, h - 16), 1, border_radius=8)
    if title:
        f = pygame.font.SysFont("Georgia", 27, bold=True)
        ts = f.render(title, True, (255, 232, 176))
        screen.blit(ts, (x + 28, y + 22))
    if subtitle:
        sf = pygame.font.SysFont("Arial", 16)
        ss = sf.render(subtitle, True, (225, 215, 195))
        screen.blit(ss, (x + 28, y + 61))


def menu_button_layout(W, H):
    """Return the exact menu button rectangles used for drawing AND mouse input."""
    card_top = int(H * 0.19)
    bottom_reserved = int(H * 0.37)
    card_h = max(190, int(H * 0.43))
    card_h = min(card_h, H - card_top - bottom_reserved)
    card_gap = max(7, int(W * 0.008))
    side_margin = max(24, int(W * 0.055))
    card_w = int((W - side_margin * 2 - card_gap * 4) / 5)
    card_w = max(110, card_w)
    btn_gap_x = max(12, int(W * 0.012))
    btn_gap_y = max(10, int(H * 0.020))
    row_width = min(W - 70, int(W * 0.78))
    btn_w = int((row_width - btn_gap_x * 2) / 3)
    btn_h = max(58, min(78, int(H * 0.095)))
    row1_y = card_top + card_h + max(18, int(H * 0.025))
    row2_y = row1_y + btn_h + btn_gap_y
    row1 = ["story", "attack", "characters"]
    row2 = ["quiz", "settings"]
    x0 = (W - (btn_w * 3 + btn_gap_x * 2)) // 2
    rects = []
    for i, key in enumerate(row1):
        rects.append((key, pygame.Rect(x0 + i * (btn_w + btn_gap_x), row1_y, btn_w, btn_h)))
    row2_total = btn_w * 2 + btn_gap_x
    x2 = (W - row2_total) // 2
    for i, key in enumerate(row2):
        rects.append((key, pygame.Rect(x2 + i * (btn_w + btn_gap_x), row2_y, btn_w, btn_h)))
    return rects


def quiz_option_layout(W, H, count):
    """Centralized quiz answer cards; kept clear of both side characters."""
    qx = max(250, int(W * 0.235))
    qw = min(int(W * 0.53), W - qx * 2)
    top = int(H * 0.595)
    gap = max(9, int(H * 0.014))
    h = max(45, min(56, int(H * 0.072)))
    return [pygame.Rect(qx, top + i * (h + gap), qw, h) for i in range(count)]


def quiz_popup_layout(W, H):
    panel_w = min(700, W - 110)
    panel_h = min(390, H - 110)
    panel = pygame.Rect((W - panel_w) // 2, (H - panel_h) // 2, panel_w, panel_h)
    button_w = min(500, panel.w - 90)
    button = pygame.Rect(panel.centerx - button_w // 2, panel.bottom - 68, button_w, 48)
    return panel, button

def draw_menu(screen, backgrounds, W, H, big_font, sub_font, text_font, small_font, hover=None):
    """Main menu: centered title, character showcase, clean interactive mode buttons.

    FIX38 UI changes:
    - Removed the stray "PILIH MODE" header.
    - Removed all small descriptions under the mode buttons.
    - Removed emoji icons (font compatibility issues on Windows).
    - Rebalanced the layout so the title never collides with the character cards.
    - Character cards sit above the mode buttons, matching the requested reference.
    """
    draw_background(screen, backgrounds, "ui_batik", W, H)

    # Decorative theatre frame.
    frame = pygame.Rect(10, 10, W - 20, H - 20)
    pygame.draw.rect(screen, (118, 78, 29), frame, 2, border_radius=18)
    pygame.draw.rect(screen, (45, 30, 18), frame.inflate(-18, -18), 1, border_radius=16)

    # ------------------------------------------------------------
    # Title block: intentionally no "PILIH MODE" text here.
    # ------------------------------------------------------------
    title_font = pygame.font.SysFont("Georgia", max(38, min(58, int(H * 0.075))), bold=True)
    tagline_font = pygame.font.SysFont("Georgia", max(20, min(30, int(H * 0.038))), bold=True)
    title = title_font.render("E-DALANG", True, (122, 38, 18))
    tagline = tagline_font.render("EXPERIENCE THE WAYANG DIFFERENTLY", True, (84, 50, 24))
    title_y = max(32, int(H * 0.045))
    screen.blit(title, title.get_rect(center=(W // 2, title_y + title.get_height() // 2)))
    screen.blit(tagline, tagline.get_rect(center=(W // 2, title_y + title.get_height() + 8 + tagline.get_height() // 2)))

    # ------------------------------------------------------------
    # Character showcase.
    # ------------------------------------------------------------
    card_top = int(H * 0.19)
    bottom_reserved = int(H * 0.37)
    card_h = max(190, int(H * 0.43))
    card_h = min(card_h, H - card_top - bottom_reserved)
    card_gap = max(7, int(W * 0.008))
    side_margin = max(24, int(W * 0.055))
    card_w = int((W - side_margin * 2 - card_gap * (len(CHARACTERS) - 1)) / len(CHARACTERS))
    card_w = max(110, card_w)
    total_w = card_w * len(CHARACTERS) + card_gap * (len(CHARACTERS) - 1)
    start_x = (W - total_w) // 2

    mini_title = pygame.font.SysFont("Georgia", max(15, min(22, int(card_w * 0.115))), bold=True)
    mini_desc = pygame.font.SysFont("Arial", max(8, min(12, int(card_w * 0.060))))

    for i, char in enumerate(CHARACTERS):
        x = start_x + i * (card_w + card_gap)
        r = pygame.Rect(x, card_top, card_w, card_h)
        draw_gold_panel(screen, r, None, None, False)

        ts = mini_title.render(char["name"], True, (255, 232, 176))
        screen.blit(ts, ts.get_rect(center=(x + card_w // 2, card_top + 26)))

        try:
            img = pygame.image.load(str(ASSETS / char["file"])).convert_alpha()
            bbox = img.get_bounding_rect(min_alpha=8)
            if bbox.width > 2 and bbox.height > 2:
                img = img.subsurface(bbox).copy()
            max_img_w = card_w - 18
            max_img_h = card_h - 86
            scale = min(max_img_w / img.get_width(), max_img_h / img.get_height())
            img = pygame.transform.smoothscale(
                img,
                (max(1, int(img.get_width() * scale)), max(1, int(img.get_height() * scale)))
            )
            screen.blit(img, img.get_rect(center=(x + card_w // 2, card_top + card_h // 2 + 4)))
        except Exception as exc:
            print(f"[WARNING] Preview karakter {char['name']}: {exc}")

        # Keep the character's trait inside its card.  This is deliberately
        # compact so long traits can never collide with neighboring cards.
        desc_lines = wrap_text(mini_desc, char["desc"], card_w - 18)[:3]
        line_h = mini_desc.get_height() + 1
        dy = card_top + card_h - 10 - line_h * len(desc_lines)
        for line in desc_lines:
            ds = mini_desc.render(line, True, (225, 215, 195))
            screen.blit(ds, ds.get_rect(center=(x + card_w // 2, dy + line_h // 2)))
            dy += line_h

    # ------------------------------------------------------------
    # Mode buttons: title only.  No description text underneath.
    # ------------------------------------------------------------
    buttons = [
        ("MODE STORY", "story"),
        ("GESTURE ATTACK", "attack"),
        ("PILIH KARAKTER", "characters"),
        ("MODE QUIZ", "quiz"),
        ("PENGATURAN", "settings"),
    ]

    layout = dict(menu_button_layout(W, H))
    btn_h = next(iter(layout.values())).h if layout else 64
    rects = []
    button_font = pygame.font.SysFont("Georgia", max(20, min(30, int(btn_h * 0.39))), bold=True)
    for label, key in buttons:
        r = layout[key]
        rects.append((key, r))
        draw_gold_panel(screen, r, None, None, hover == key)
        ts = button_font.render(label, True, (255, 232, 176))
        # Fit long labels such as GESTURE ATTACK without overflowing.
        if ts.get_width() > r.w - 22:
            fit_font = pygame.font.SysFont("Georgia", max(16, int(button_font.get_height() * 0.80)), bold=True)
            ts = fit_font.render(label, True, (255, 232, 176))
        screen.blit(ts, ts.get_rect(center=r.center))

    # Minimal control hint.  No additional menu descriptions.
    foot_font = pygame.font.SysFont("Arial", max(12, min(17, int(H * 0.022))))
    foot = foot_font.render("1 Story  •  2 Attack  •  3 Karakter  •  4 Quiz  •  5 Pengaturan  •  ESC keluar", True, (84, 50, 24))
    foot_y = H - max(18, int(H * 0.025))
    screen.blit(foot, foot.get_rect(center=(W // 2, foot_y)))
    return rects

# ---------------------------------------------------------------------------
# Layar Pilih Karakter (gaya galeri karakter): grid kartu di kiri, pratinjau
# besar di tengah, info dan pilihan pemain di kanan. Font dan gambar di-cache
# agar tidak dimuat ulang setiap frame.
# ---------------------------------------------------------------------------
_UI_FONTS = {}
_UI_IMGS = {}


def ui_font(name, size, bold=False):
    key = (name, size, bold)
    f = _UI_FONTS.get(key)
    if f is None:
        f = pygame.font.SysFont(name, size, bold=bold)
        _UI_FONTS[key] = f
    return f


def fit_font(name, text, max_w, size, min_size=12, bold=False):
    while size > min_size and ui_font(name, size, bold).size(text)[0] > max_w:
        size -= 1
    return ui_font(name, size, bold)


def char_image(filename, max_w, max_h):
    key = (filename, int(max_w), int(max_h))
    img = _UI_IMGS.get(key)
    if img is None:
        raw = pygame.image.load(str(ASSETS / filename)).convert_alpha()
        bbox = raw.get_bounding_rect(min_alpha=8)
        if bbox.width > 2 and bbox.height > 2:
            raw = raw.subsurface(bbox).copy()
        sc = min(max_w / raw.get_width(), max_h / raw.get_height())
        img = pygame.transform.smoothscale(raw, (max(1, int(raw.get_width() * sc)), max(1, int(raw.get_height() * sc))))
        _UI_IMGS[key] = img
    return img


def soft_glow(w, h, color=(240, 176, 64)):
    key = ("glow", int(w), int(h), color)
    surf = _UI_IMGS.get(key)
    if surf is None:
        surf = pygame.Surface((int(w), int(h)), pygame.SRCALPHA)
        steps = 30
        for i in range(steps):
            f = 1 - i / steps
            ew, eh = max(2, int(w * f)), max(2, int(h * f))
            alpha = int(4 + 62 * (i / steps) ** 2)
            pygame.draw.ellipse(surf, (*color, alpha), pygame.Rect((int(w) - ew) // 2, (int(h) - eh) // 2, ew, eh))
        _UI_IMGS[key] = surf
    return surf


def slot_badge(screen, center, number):
    col = (238, 181, 70) if number == 1 else (196, 64, 42)
    txt = (40, 26, 12) if number == 1 else (255, 240, 220)
    pygame.draw.circle(screen, (20, 12, 8), center, 14)
    pygame.draw.circle(screen, col, center, 12)
    t = ui_font("Georgia", 16, True).render(str(number), True, txt)
    screen.blit(t, t.get_rect(center=center))


def draw_character_menu(screen, backgrounds, W, H, big_font, sub_font, text_font, small_font, left_idx, right_idx, slot, hover=None):
    """Return (cards, back, slot_tabs) berupa rect untuk hit-test klik."""
    mx, my = logical_mouse()
    draw_background(screen, backgrounds, "hutan_sore", W, H)
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((8, 5, 3, 200))
    screen.blit(overlay, (0, 0))

    m = max(28, int(W * 0.035))
    active_idx = left_idx if slot == 0 else right_idx
    now = pygame.time.get_ticks() / 1000.0

    # --- Header -------------------------------------------------------
    title = ui_font("Georgia", max(30, int(H * 0.055)), True).render("PILIH KARAKTER", True, (255, 222, 157))
    screen.blit(title, (m, int(H * 0.03)))
    sub = ui_font("Arial", max(14, int(H * 0.023))).render(
        "Pilih karakter untuk Gesture Attack. Story tetap memakai Bima dan Arjuna.", True, (215, 203, 180))
    screen.blit(sub, (m, int(H * 0.03) + title.get_height() + 2))

    back = pygame.Rect(W - m - 52, int(H * 0.03), 52, 52)
    back_hot = back.collidepoint(mx, my) or hover == "back"
    pygame.draw.circle(screen, (46, 32, 20) if back_hot else (35, 24, 16), back.center, 26)
    pygame.draw.circle(screen, (238, 181, 70) if back_hot else (154, 105, 39), back.center, 26, 3)
    cx0, cy0 = back.center
    pygame.draw.polygon(screen, (255, 226, 158), [(cx0 - 12, cy0), (cx0 - 1, cy0 - 10), (cx0 - 1, cy0 - 4),
                                                  (cx0 + 11, cy0 - 4), (cx0 + 11, cy0 + 4), (cx0 - 1, cy0 + 4),
                                                  (cx0 - 1, cy0 + 10)])

    # --- Grid kartu karakter (kiri) -----------------------------------
    cols = 2
    gap = max(10, int(W * 0.009))
    cw = int(W * 0.108)
    ch = int(cw * 1.26)
    gx, gy = m, int(H * 0.18)
    cards = []
    for i, char in enumerate(CHARACTERS):
        r = pygame.Rect(gx + (i % cols) * (cw + gap), gy + (i // cols) * (ch + gap), cw, ch)
        cards.append((i, r))
        hot = r.collidepoint(mx, my)
        is_active = i == active_idx
        assigned = i in (left_idx, right_idx)

        sh = pygame.Surface((cw + 8, ch + 8), pygame.SRCALPHA)
        sh.fill((0, 0, 0, 100))
        screen.blit(sh, (r.x + 4, r.y + 6))
        body = pygame.Surface((cw, ch), pygame.SRCALPHA)
        body.fill((54, 39, 27, 240) if (hot or is_active) else (36, 26, 18, 235))
        screen.blit(body, r.topleft)
        if is_active:
            border, bw = (255, 244, 214), 3
        elif assigned:
            border, bw = (238, 181, 70), 2
        else:
            border, bw = (122, 86, 40), 2
        pygame.draw.rect(screen, border, r, bw, border_radius=10)

        box_h = ch - 52
        try:
            img = char_image(char["file"], cw - 16, box_h)
            screen.blit(img, img.get_rect(center=(r.centerx, r.y + 8 + box_h // 2)))
        except Exception as exc:
            print(f"[WARNING] Preview karakter {char['name']}: {exc}")

        strip = pygame.Rect(r.x + 6, r.bottom - 38, cw - 12, 30)
        pygame.draw.rect(screen, (238, 220, 184), strip, border_radius=6)
        nf = fit_font("Arial", char["name"], strip.w - 10, 15, 10, True)
        nt = nf.render(char["name"], True, (62, 38, 20))
        screen.blit(nt, nt.get_rect(center=strip.center))

        bx = r.x + 20
        if left_idx == i:
            slot_badge(screen, (bx, r.y + 20), 1)
            bx += 28
        if right_idx == i:
            slot_badge(screen, (bx, r.y + 20), 2)

    # --- Pratinjau besar (tengah) -------------------------------------
    area_l = gx + cols * cw + (cols - 1) * gap + 30
    right_x = W - m - int(W * 0.30)
    cx = (area_l + right_x) // 2
    cy = int(H * 0.52)
    glow = soft_glow(int((right_x - area_l) * 1.05), int(H * 0.88))
    screen.blit(glow, glow.get_rect(center=(cx, cy)))
    active_char = CHARACTERS[active_idx]
    try:
        prev = char_image(active_char["file"], right_x - area_l - 20, int(H * 0.70))
        foot_y = int(cy + H * 0.35)
        bob = math.sin(now * 1.6) * 4
        fs = pygame.Surface((max(40, int(prev.get_width() * 0.8)), 26), pygame.SRCALPHA)
        pygame.draw.ellipse(fs, (0, 0, 0, 120), fs.get_rect())
        screen.blit(fs, fs.get_rect(center=(cx, foot_y + 2)))
        screen.blit(prev, prev.get_rect(midbottom=(cx, int(foot_y + bob))))
    except Exception as exc:
        print(f"[WARNING] Pratinjau karakter: {exc}")

    # --- Info karakter (kanan) ----------------------------------------
    px, pw = right_x, W - m - right_x
    py = int(H * 0.19)
    nf = fit_font("Georgia", active_char["name"], pw, max(30, int(H * 0.06)), 20, True)
    name = nf.render(active_char["name"], True, (255, 222, 157))
    screen.blit(name, (px, py))
    ly = py + name.get_height() + 8
    pygame.draw.line(screen, (190, 138, 52), (px, ly), (px + pw, ly), 2)
    dx = px + pw // 2
    pygame.draw.polygon(screen, (238, 181, 70), [(dx, ly - 6), (dx + 6, ly), (dx, ly + 6), (dx - 6, ly)])
    lab = ui_font("Arial", 14, True).render("SIFAT", True, (190, 138, 52))
    screen.blit(lab, (px, ly + 16))
    body_font = ui_font("Arial", max(17, int(H * 0.028)))
    yy = ly + 16 + lab.get_height() + 6
    for line in wrap_text(body_font, active_char["desc"], pw):
        ls = body_font.render(line, True, (235, 225, 205))
        screen.blit(ls, (px, yy))
        yy += body_font.get_height() + 4

    # --- Pilihan pemain (kanan bawah) ---------------------------------
    tab_h, tab_gap = 58, 10
    ty1 = H - 56 - tab_h
    ty0 = ty1 - tab_gap - tab_h
    cap = ui_font("Arial", 14, True).render("KARAKTER UNTUK", True, (190, 138, 52))
    screen.blit(cap, (px, ty0 - cap.get_height() - 8))
    slot_tabs = []
    for si, idx in enumerate((left_idx, right_idx)):
        r = pygame.Rect(px, ty0 + si * (tab_h + tab_gap), pw, tab_h)
        slot_tabs.append((si, r))
        draw_gold_panel(screen, r, None, None, slot == si)
        if slot != si and r.collidepoint(mx, my):
            pygame.draw.rect(screen, (200, 150, 70), r, 2, border_radius=10)
        slot_badge(screen, (r.x + 32, r.centery), si + 1)
        lbl = ui_font("Georgia", 20, True).render(f"PEMAIN {si + 1}", True, (255, 232, 176))
        screen.blit(lbl, lbl.get_rect(midleft=(r.x + 58, r.centery)))
        nm = ui_font("Arial", 17, True).render(CHARACTERS[idx]["name"], True, (255, 244, 214) if slot == si else (215, 200, 170))
        screen.blit(nm, nm.get_rect(midright=(r.right - 18, r.centery)))

    hint = ui_font("Arial", 15).render(
        "Tekan 1 / 2 untuk memilih pemain  •  Klik kartu untuk memilih karakter  •  ESC kembali", True, (200, 188, 165))
    screen.blit(hint, hint.get_rect(center=(W // 2, H - 22)))
    return cards, back, slot_tabs


def draw_settings(screen, backgrounds, W, H, big_font, text_font, small_font, show_pov, music_on):
    draw_background(screen, backgrounds, "hutan_sore", W, H)
    overlay = pygame.Surface((W,H), pygame.SRCALPHA); overlay.fill((5,4,3,190)); screen.blit(overlay,(0,0))
    title = big_font.render("PENGATURAN", True, (255,222,157)); screen.blit(title, title.get_rect(center=(W//2,85)))
    rows = [
        ("POV TANGAN", "Jendela kamera terpisah", show_pov),
        ("MUSIK", "Musik latar mode story", music_on),
    ]
    rects=[]
    for i,(name,desc,on) in enumerate(rows):
        r=pygame.Rect(W//2-330,180+i*125,660,92); rects.append(r)
        draw_gold_panel(screen,r,name,desc,False)
        status=small_font.render("AKTIF" if on else "NONAKTIF",True,(255,225,160) if on else (190,180,165))
        screen.blit(status,status.get_rect(midright=(r.right-25,r.centery)))
    back=pygame.Rect(45,H-70,180,45); draw_gold_panel(screen,back,"KEMBALI","",False)
    hint=small_font.render("Klik pengaturan untuk mengubah • ESC kembali",True,(225,215,195)); screen.blit(hint,hint.get_rect(center=(W//2,H-35)))
    return rects,back


def _load_character_image(char_name, target_height):
    """Load a menu/quiz character image, crop transparent padding and scale it."""
    char = next((c for c in CHARACTERS if c["name"] == char_name), None)
    if not char:
        return None
    path = ASSETS / char["file"]
    if not path.exists():
        return None
    try:
        img = pygame.image.load(str(path)).convert_alpha()
        bbox = img.get_bounding_rect(min_alpha=8)
        if bbox.width > 2 and bbox.height > 2:
            img = img.subsurface(bbox).copy()
        ratio = target_height / max(1, img.get_height())
        img = pygame.transform.smoothscale(img, (max(1, int(img.get_width()*ratio)), max(1, int(img.get_height()*ratio))))
        return img, char.get("source_facing", 1)
    except Exception as exc:
        print(f"[WARNING] Gagal memuat karakter {char_name}: {exc}")
        return None


def _inward_character(screen, char_name, center, target_height, wanted_facing):
    loaded = _load_character_image(char_name, target_height)
    if not loaded:
        return
    img, source_facing = loaded
    if source_facing != wanted_facing:
        img = pygame.transform.flip(img, True, False)
    rect = img.get_rect(center=(int(center[0]), int(center[1])))
    # Subtle glow silhouette like the reference UI.
    try:
        mask = pygame.mask.from_surface(img, 8)
        halo = mask.to_surface(setcolor=(205, 151, 53, 120), unsetcolor=(0, 0, 0, 0))
        halo.set_colorkey((0, 0, 0, 0))
        screen.blit(halo, (rect.x-2, rect.y-2))
    except Exception:
        pass
    screen.blit(img, rect)


def _draw_quiz_answer_card(screen, rect, number, text, font, selected=False, correct=False, wrong=False, hover=False):
    """Draw one clean answer card; text is vertically centered and never shares a title row."""
    if correct:
        border = (94, 190, 112)
    elif wrong:
        border = (204, 76, 76)
    elif selected or hover:
        border = (238, 181, 70)
    else:
        border = (154, 105, 39)
    shadow = pygame.Surface((rect.w + 8, rect.h + 8), pygame.SRCALPHA)
    shadow.fill((0, 0, 0, 105))
    screen.blit(shadow, (rect.x + 4, rect.y + 5))
    pygame.draw.rect(screen, (35, 24, 16), rect, border_radius=10)
    pygame.draw.rect(screen, border, rect, 2, border_radius=10)
    pygame.draw.rect(screen, (76, 51, 27), rect.inflate(-8, -8), 1, border_radius=8)

    cx = rect.x + 35
    pygame.draw.circle(screen, (25, 18, 11), (cx, rect.centery), 17)
    pygame.draw.circle(screen, border, (cx, rect.centery), 17, 2)
    ns = pygame.font.SysFont("Georgia", 21, bold=True).render(str(number), True, (255, 231, 169))
    screen.blit(ns, ns.get_rect(center=(cx, rect.centery + 1)))

    available = rect.w - 82
    fs = font
    if fs.size(text)[0] > available:
        fs = pygame.font.SysFont("Arial", max(16, min(23, font.get_height() - 2)))
    lines = wrap_text(fs, text, available)
    if len(lines) > 2:
        fs = pygame.font.SysFont("Arial", max(15, fs.get_height() - 2))
        lines = wrap_text(fs, text, available)[:2]
    total_h = len(lines) * fs.get_height()
    yy = rect.centery - total_h // 2
    for line in lines:
        surf = fs.render(line, True, (255, 239, 210))
        screen.blit(surf, surf.get_rect(midleft=(rect.x + 66, yy + fs.get_height() // 2)))
        yy += fs.get_height()


def _draw_quiz_popup(screen, W, H, q, selected, quiz_index, font, small_font):
    """Reference-style correct/wrong popup shown after an answer is selected."""
    correct = selected == q["answer"]
    dim = pygame.Surface((W, H), pygame.SRCALPHA)
    dim.fill((0, 0, 0, 175))
    screen.blit(dim, (0, 0))

    panel, button = quiz_popup_layout(W, H)
    outer = (74, 185, 112) if correct else (211, 73, 73)
    inner = (13, 55, 35) if correct else (66, 25, 23)
    pygame.draw.rect(screen, (18, 12, 8), panel, border_radius=24)
    pygame.draw.rect(screen, outer, panel, 4, border_radius=24)
    pygame.draw.rect(screen, (157, 109, 44), panel.inflate(-12, -12), 2, border_radius=18)

    icon_center = (panel.centerx, panel.y + 68)
    pygame.draw.circle(screen, inner, icon_center, 48)
    pygame.draw.circle(screen, outer, icon_center, 48, 3)
    if correct:
        pygame.draw.line(screen, (255, 232, 170), (icon_center[0]-20, icon_center[1]+2), (icon_center[0]-5, icon_center[1]+17), 7)
        pygame.draw.line(screen, (255, 232, 170), (icon_center[0]-5, icon_center[1]+17), (icon_center[0]+23, icon_center[1]-19), 7)
    else:
        pygame.draw.line(screen, (255, 215, 190), (icon_center[0]-18, icon_center[1]-18), (icon_center[0]+18, icon_center[1]+18), 7)
        pygame.draw.line(screen, (255, 215, 190), (icon_center[0]+18, icon_center[1]-18), (icon_center[0]-18, icon_center[1]+18), 7)

    title = "BENAR!" if correct else "SALAH!"
    subtitle = "Hebat! Jawaban Anda tepat." if correct else "Coba lagi! Jawaban kurang tepat."
    tf = pygame.font.SysFont("Georgia", 42, bold=True)
    sf = pygame.font.SysFont("Arial", 22, bold=True)
    ts = tf.render(title, True, (245, 239, 220))
    ss = sf.render(subtitle, True, (238, 228, 207))
    screen.blit(ts, ts.get_rect(center=(panel.centerx, panel.y + 142)))
    screen.blit(ss, ss.get_rect(center=(panel.centerx, panel.y + 178)))

    explanation = q.get("explanation", "")
    ef = pygame.font.SysFont("Arial", 20)
    lines = wrap_text(ef, explanation, panel.w - 100)[:3]
    yy = panel.y + 210
    for line in lines:
        es = ef.render(line, True, (232, 223, 204))
        screen.blit(es, es.get_rect(center=(panel.centerx, yy)))
        yy += 26

    button_fill = (31, 100, 55) if correct else (112, 35, 35)
    pygame.draw.rect(screen, button_fill, button, border_radius=10)
    pygame.draw.rect(screen, outer, button, 2, border_radius=10)
    label = "LANJUTKAN KE PERTANYAAN BERIKUTNYA" if correct else "ULANGI PERTANYAAN"
    bs = pygame.font.SysFont("Arial", 20, bold=True).render(label, True, (255, 244, 220))
    screen.blit(bs, bs.get_rect(center=button.center))

    step = small_font.render(f"Soal {quiz_index + 1:02d}", True, (226, 207, 169))
    screen.blit(step, step.get_rect(center=(panel.centerx, panel.y + 28)))
    return button


def draw_quiz_ui(screen, backgrounds, W, H, big_font, sub_font, text_font, small_font, quiz_index, quiz_score, selected, finished=False):
    """Clean audience quiz layout based on the supplied reference."""
    draw_background(screen, backgrounds, "ui_edalang", W, H)
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((5, 4, 3, 150))
    screen.blit(overlay, (0, 0))

    frame = pygame.Rect(14, 14, W - 28, H - 28)
    pygame.draw.rect(screen, (160, 109, 39), frame, 2, border_radius=16)
    pygame.draw.rect(screen, (63, 42, 23), frame.inflate(-14, -14), 1, border_radius=12)

    title_font = pygame.font.SysFont("Georgia", max(38, min(52, int(H * 0.070))), bold=True)
    title = title_font.render("KUIS PENONTON", True, (255, 224, 155))
    screen.blit(title, title.get_rect(center=(W // 2, 58)))

    side_h = min(245, max(185, int(H * 0.33)))
    _inward_character(screen, "BIMA", (max(120, int(W * 0.11)), int(H * 0.57)), side_h, 1)
    _inward_character(screen, "ARJUNA", (min(W - 120, int(W * 0.89)), int(H * 0.57)), side_h, -1)

    count = len(QUIZ_QUESTIONS)
    rail_w = min(430, int(W * 0.36))
    rail = pygame.Rect((W - rail_w) // 2, 108, rail_w, 54)
    pygame.draw.rect(screen, (24, 16, 9), rail, border_radius=20)
    pygame.draw.rect(screen, (151, 99, 33), rail, 2, border_radius=20)
    label = small_font.render("PERJALANAN CERITA", True, (238, 203, 141))
    screen.blit(label, label.get_rect(center=(W // 2, 120)))
    x0, x1 = rail.x + 35, rail.right - 35
    yline = 143
    pygame.draw.line(screen, (193, 137, 51), (x0, yline), (x1, yline), 3)
    for i in range(count):
        x = int(x0 + (x1 - x0) * (i / max(1, count - 1)))
        active = i <= quiz_index if not finished else True
        pygame.draw.circle(screen, (255, 210, 101) if active else (31, 23, 15), (x, yline), 9)
        pygame.draw.circle(screen, (132, 89, 31), (x, yline), 9, 2)

    num_box = pygame.Rect(W // 2 - 58, 166, 116, 38)
    draw_gold_panel(screen, num_box, None, None, False)
    num = small_font.render(f"{quiz_index + 1:02d} / {count:02d}" if not finished else f"{count:02d} / {count:02d}", True, (255, 231, 169))
    screen.blit(num, num.get_rect(center=num_box.center))

    if finished:
        result = pygame.Rect(max(170, W // 2 - 330), 245, min(660, W - 340), 285)
        draw_gold_panel(screen, result, "KUIS SELESAI", None, True)
        score = sub_font.render(f"SKOR {quiz_score} / {count}", True, (255, 231, 169))
        screen.blit(score, score.get_rect(center=(W // 2, 330)))
        msg = ("Luar biasa! Kamu memahami kisahnya dengan sangat baik." if quiz_score == count
               else "Bagus! Kamu sudah memahami sebagian besar pesan cerita." if quiz_score >= 3
               else "Tetap semangat! Coba ingat kembali perjalanan Bima dan Arjuna.")
        yy = 385
        for line in wrap_text(text_font, msg, result.w - 80)[:3]:
            ss = text_font.render(line, True, (235, 225, 205))
            screen.blit(ss, ss.get_rect(center=(W // 2, yy)))
            yy += 30
        hint = small_font.render("M / ESC / KEMBALI = menu utama", True, (255, 226, 163))
        screen.blit(hint, hint.get_rect(center=(W // 2, H - 35)))
        return [], pygame.Rect(34, H - 68, 205, 46), None

    q = QUIZ_QUESTIONS[quiz_index]
    qx = max(270, int(W * 0.22))
    qw = min(int(W * 0.56), W - qx * 2)
    qhead = pygame.Rect(qx, 222, qw, 44)
    qbox = pygame.Rect(qx, 266, qw, 118)

    pygame.draw.rect(screen, (35, 24, 16), qbox, border_radius=12)
    pygame.draw.rect(screen, (154, 105, 39), qbox, 2, border_radius=12)
    pygame.draw.rect(screen, (75, 50, 26), qbox.inflate(-8, -8), 1, border_radius=9)
    pygame.draw.rect(screen, (29, 19, 11), qhead, border_radius=10)
    pygame.draw.rect(screen, (238, 181, 70), qhead, 2, border_radius=10)

    qtitle_font = pygame.font.SysFont("Georgia", 25, bold=True)
    qtitle = qtitle_font.render(f"PERTANYAAN {quiz_index + 1:02d}", True, (255, 232, 176))
    screen.blit(qtitle, qtitle.get_rect(center=(qhead.centerx, qhead.centery)))

    qfont = pygame.font.SysFont("Georgia", max(22, min(30, int(H * 0.040))), bold=False)
    q_lines = wrap_text(qfont, q["question"], qbox.w - 60)
    if len(q_lines) > 2:
        qfont = pygame.font.SysFont("Georgia", max(20, qfont.get_height() - 2))
        q_lines = wrap_text(qfont, q["question"], qbox.w - 60)[:2]
    total_h = len(q_lines) * qfont.get_height()
    yy = qbox.centery - total_h // 2
    for line in q_lines:
        qs = qfont.render(line, True, (255, 239, 204))
        screen.blit(qs, qs.get_rect(center=(qbox.centerx, yy + qfont.get_height() // 2)))
        yy += qfont.get_height()

    option_rects = quiz_option_layout(W, H, len(q["options"]))
    mouse_pos = logical_mouse()
    for idx, (r, option) in enumerate(zip(option_rects, q["options"])):
        is_selected = selected == idx
        correct = selected is not None and idx == q["answer"]
        wrong = selected == idx and idx != q["answer"]
        hover = selected is None and r.collidepoint(mouse_pos)
        _draw_quiz_answer_card(screen, r, idx + 1, option, text_font, is_selected, correct, wrong, hover)

    hint = small_font.render("Pilih jawaban dengan klik atau tekan 1, 2, 3, 4", True, (255, 226, 163))
    screen.blit(hint, hint.get_rect(center=(W // 2, H - 30)))
    back = pygame.Rect(34, H - 68, 205, 46)
    draw_gold_panel(screen, back, "KEMBALI", None, False)

    popup_button = None
    if selected is not None:
        popup_button = _draw_quiz_popup(screen, W, H, q, selected, quiz_index, text_font, small_font)
    return option_rects, back, popup_button

def draw_attack(screen, backgrounds, W, H, big_font, text_font, small_font, bima, arjuna, left_name, right_name, bima_attacking=False, arjuna_attacking=False):
    draw_background(screen, backgrounds, "ui_batik", W, H)
    top=pygame.Surface((W,86),pygame.SRCALPHA); top.fill((18,12,7,210)); screen.blit(top,(0,0))
    title=big_font.render("GESTURE ATTACK",True,(255,216,125)); screen.blit(title,(35,18))
    info=text_font.render(f"Pemain 1: {left_name}   |   Pemain 2: {right_name}",True,(235,225,205)); screen.blit(info,(W-540,28))
    pygame.draw.line(screen,(150,98,44),(W//2,115),(W//2,H-45),2)
    STYLE["halo"] = "dark"
    try:
        bima.draw(screen); arjuna.draw(screen)
    finally:
        STYLE["halo"] = "gold"
    if bima_attacking:
        fx=pygame.Surface((150,150),pygame.SRCALPHA); pygame.draw.circle(fx,(214,70,32,140),(75,75),55,5); screen.blit(fx,fx.get_rect(center=(bima.pos.x+75,bima.pos.y)))
        s=small_font.render("SERANG!",True,(170,34,18)); screen.blit(s,(bima.pos.x-55,bima.pos.y-245))
    if arjuna_attacking:
        fx=pygame.Surface((150,150),pygame.SRCALPHA); pygame.draw.circle(fx,(214,70,32,140),(75,75),55,5); screen.blit(fx,fx.get_rect(center=(arjuna.pos.x-75,arjuna.pos.y)))
        s=small_font.render("SERANG!",True,(170,34,18)); screen.blit(s,(arjuna.pos.x-55,arjuna.pos.y-245))
    panel=pygame.Surface((W-80,72),pygame.SRCALPHA); panel.fill((10,8,6,200)); screen.blit(panel,(40,H-95))
    help_s=small_font.render("TELAPAK = GERAK / SIAGA    •    KEPAL = SERANG    •    V = POV    •    C = GANTI KARAKTER    •    M = MENU    •    ESC = KELUAR",True,(245,235,215))
    screen.blit(help_s,help_s.get_rect(center=(W//2,H-59)))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera", type=int, default=None)
    parser.add_argument("--projector", action="store_true")
    args = parser.parse_args()

    if args.camera is not None:
        CONFIG["window"]["camera_index"] = args.camera

    pygame.init()
    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    except pygame.error as exc:
        print(f"[WARNING] Audio mixer gagal: {exc}")

    W = int(CONFIG["window"]["width"])
    H = int(CONFIG["window"]["height"])
    pygame.display.set_mode((W, H), pygame.RESIZABLE)
    screen = pygame.Surface((W, H))  # kanvas logis; ditampilkan lewat present_canvas()
    pygame.display.set_caption("Bima dan Arjuna – Janji di Tengah Hutan")
    clock = pygame.time.Clock()
    audio = Audio()
    backgrounds = load_backgrounds((W, H))
    validate_story_assets()
    audio.preload_all()

    camera_index = int(CONFIG["window"]["camera_index"])
    cam = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    # Keep the camera responsive: MediaPipe does not need a 1280x720 frame.
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if not cam.isOpened():
        print(f"[WARNING] Kamera {camera_index} tidak tersedia. Program tetap berjalan tanpa tracking tangan.")
        cam = None

    detector = None
    try:
        import mediapipe as mp
        detector = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.55,
            min_tracking_confidence=0.55,
            model_complexity=1,
        )
    except Exception as exc:
        print(f"[WARNING] MediaPipe tidak siap: {exc}. Wayang tetap bisa dimainkan dengan tombol/otomatis.")

    puppet_cfg = CONFIG["puppet"]
    bima = make_puppet("bima_new.png", puppet_cfg["left_start_x"], puppet_cfg["left_start_y"], puppet_cfg["target_height"], puppet_cfg["left_offset_x"], puppet_cfg["left_offset_y"])
    arjuna = make_puppet("arjuna_new.png", puppet_cfg["right_start_x"], puppet_cfg["right_start_y"], puppet_cfg["target_height"], puppet_cfg["right_offset_x"], puppet_cfg["right_offset_y"])
    # Aset Bima baru menghadap kiri secara asli. Untuk tampilan story dan
    # posisi awal, Bima tetap menghadap ke kanan (ke arah Arjuna).
    bima.set_visual_facing(1, -1)
    # Arjuna menghadap kiri secara asli, sehingga tetap menghadap ke Bima.
    arjuna.set_visual_facing(-1, -1)
    bima_gesture = GestureStabilizer(int(CONFIG["gesture"]["required_frames"]))
    arjuna_gesture = GestureStabilizer(int(CONFIG["gesture"]["required_frames"]))
    attack_left_state = 1
    attack_right_state = 1
    attack_left_puppet = bima
    attack_right_puppet = arjuna

    def rebuild_attack_puppets():
        nonlocal attack_left_puppet, attack_right_puppet
        lc = CHARACTERS[flow.char_left_idx]
        rc = CHARACTERS[flow.char_right_idx]
        attack_left_puppet = make_puppet(lc["file"], 385, 470, puppet_cfg["target_height"], puppet_cfg["left_offset_x"], puppet_cfg["left_offset_y"])
        attack_right_puppet = make_puppet(rc["file"], 895, 470, puppet_cfg["target_height"], puppet_cfg["right_offset_x"], puppet_cfg["right_offset_y"])
        # Karakter kiri selalu menghadap ke tengah (kanan).
        # Karakter kanan selalu menghadap ke tengah (kiri).
        attack_left_puppet.set_visual_facing(1, lc.get("source_facing", 1))
        attack_right_puppet.set_visual_facing(-1, rc.get("source_facing", 1))


    flow = Flow()
    projector = args.projector
    fullscreen = False
    running = True
    camera_frame_counter = 0
    last_space_time = 0.0
    pov_mode = bool(CONFIG["window"].get("show_pov", True))
    latest_hand_result = None
    flow.settings_show_pov = pov_mode
    flow.settings_music = True

    speaker_font = pygame.font.SysFont("Arial", 34, bold=True)
    text_font = pygame.font.SysFont("Arial", 25)
    big_font = pygame.font.SysFont("Georgia", 58, bold=True)
    sub_font = pygame.font.SysFont("Georgia", 36, bold=True)
    small_font = pygame.font.SysFont("Arial", 20)

    def start_scene_narration():
        scene = STORY["scenes"][flow.scene_index]
        print(f"[NARRATION] Adegan {scene['id']} mulai: {scene['narration']}")
        play_voice(scene["narration"])

    def current_dialogue():
        scene = STORY["scenes"][flow.scene_index]
        return scene["dialogues"][flow.dialog_index]

    def play_dialogue():
        # Every dialogue item is [speaker, text, audio].
        dialogue = current_dialogue()
        if not isinstance(dialogue, (list, tuple)) or len(dialogue) != 3:
            raise ValueError(f"Format dialog harus [speaker, text, audio]: {dialogue!r}")
        speaker, text, audio_name = dialogue
        print(f"[DIALOGUE] Adegan {STORY['scenes'][flow.scene_index]['id']} | {speaker}: {text}")
        play_voice(audio_name)
        # IMPORTANT: every dialogue gets a fresh phase timer. Without this,
        # dialogue #2 inherited the timer from dialogue #1 and could be
        # considered finished immediately, skipping voices/dialogues.
        flow.phase_started = time.monotonic()

    def narration_text_for(audio_name, text):
        """Return the text exactly for the voice currently playing."""
        return text

    def play_voice(filename):
        ok = audio.play(filename)
        flow.played = True
        if not ok:
            # Do not silently skip a missing/broken voice.
            print(f"[ERROR] Voice gagal diputar: {filename}")
        return ok

    def after_pause_text():
        return AFTER_PAUSE_TEXT

    def opening_text_for_current_time():
        # Gunakan timestamp hasil jeda aktual rekaman, bukan pembagian
        # berdasarkan jumlah kata. Ini membuat teks tidak tertinggal dari suara.
        t = audio.elapsed()
        idx = len(OPENING_PAGES) - 1
        alpha = 255
        for i, (start, end) in enumerate(OPENING_TIMINGS):
            if t < end:
                idx = i
                local = max(0.0, t - start)
                alpha = 255 if local >= 0.06 else int(local / 0.06 * 255)
                break
        return OPENING_PAGES[idx], alpha, idx

    while running:
        now = time.monotonic()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = logical_pos(event.pos)
                if flow.phase == "menu":
                    # IMPORTANT: use the exact same responsive rectangles as draw_menu().
                    menu_hits = menu_button_layout(W, H)
                    for key,r in menu_hits:
                        if r.collidepoint(mx,my):
                            if key == "story": flow.enter("opening")
                            elif key == "attack": rebuild_attack_puppets(); flow.enter("attack")
                            elif key == "characters": flow.enter("characters")
                            elif key == "quiz":
                                flow.enter("quiz")
                                flow.quiz_index = 0
                                flow.quiz_score = 0
                                flow.quiz_selected = None
                                flow.quiz_finished = False
                                print("[QUIZ] Mulai kuis dari menu")
                            elif key == "settings": flow.enter("settings")
                            break
                elif flow.phase == "quiz" and flow.quiz_finished:
                    if pygame.Rect(34, H - 68, 205, 46).collidepoint(mx, my):
                        flow.enter("menu")
                elif flow.phase == "quiz" and not flow.quiz_finished:
                    back_rect = pygame.Rect(34, H - 68, 205, 46)
                    if back_rect.collidepoint(mx, my):
                        flow.enter("menu")
                    elif flow.quiz_selected is not None:
                        q = QUIZ_QUESTIONS[flow.quiz_index]
                        _, popup_button = quiz_popup_layout(W, H)
                        if popup_button.collidepoint(mx, my):
                            if flow.quiz_selected == q["answer"]:
                                if flow.quiz_index < len(QUIZ_QUESTIONS) - 1:
                                    flow.quiz_index += 1
                                    flow.quiz_selected = None
                                    flow.phase_started = time.monotonic()
                                else:
                                    flow.quiz_finished = True
                                    flow.phase_started = time.monotonic()
                                    print(f"[QUIZ] Selesai: {flow.quiz_score}/{len(QUIZ_QUESTIONS)}")
                            else:
                                flow.quiz_selected = None
                                flow.phase_started = time.monotonic()
                    else:
                        q = QUIZ_QUESTIONS[flow.quiz_index]
                        for idx, option_rect in enumerate(quiz_option_layout(W, H, len(q["options"]))):
                            if option_rect.collidepoint(mx, my):
                                flow.quiz_selected = idx
                                if idx == q["answer"]:
                                    flow.quiz_score += 1
                                    print(f"[QUIZ] Soal {flow.quiz_index + 1}: BENAR")
                                else:
                                    print(f"[QUIZ] Soal {flow.quiz_index + 1}: SALAH")
                                flow.phase_started = time.monotonic()
                                break
                elif flow.phase == "characters":
                    cards, back, slot_tabs = draw_character_menu(screen, backgrounds, W, H, big_font, sub_font, text_font, small_font, flow.char_left_idx, flow.char_right_idx, flow.character_slot)
                    if back.collidepoint(mx,my):
                        flow.enter("menu")
                    else:
                        picked = False
                        for idx,r in cards:
                            if r.collidepoint(mx,my):
                                if flow.character_slot == 0: flow.char_left_idx = idx
                                else: flow.char_right_idx = idx
                                rebuild_attack_puppets()
                                picked = True
                                break
                        if not picked:
                            for si,r in slot_tabs:
                                if r.collidepoint(mx,my):
                                    flow.character_slot = si
                                    break
                elif flow.phase == "settings":
                    rects, back = draw_settings(screen, backgrounds, W, H, big_font, text_font, small_font, pov_mode, flow.settings_music)
                    if back.collidepoint(mx,my):
                        flow.enter("menu")
                    elif rects[0].collidepoint(mx,my):
                        pov_mode = not pov_mode; flow.settings_show_pov = pov_mode
                        if not pov_mode: update_pov_window(None,None,False)
                    elif rects[1].collidepoint(mx,my):
                        flow.settings_music = not flow.settings_music
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if flow.phase in ("menu", "characters", "settings"):
                        if flow.phase == "menu":
                            running = False
                        else:
                            flow.enter("menu")
                    else:
                        running = False
                elif flow.phase == "menu" and event.key == pygame.K_1:
                    flow.enter("opening")
                elif flow.phase == "menu" and event.key == pygame.K_2:
                    rebuild_attack_puppets(); flow.enter("attack")
                elif flow.phase == "menu" and event.key == pygame.K_3:
                    flow.enter("characters")
                elif flow.phase == "menu" and event.key == pygame.K_4:
                    flow.enter("quiz")
                    flow.quiz_index = 0
                    flow.quiz_score = 0
                    flow.quiz_selected = None
                    flow.quiz_finished = False
                    print("[QUIZ] Mulai kuis dari menu")
                elif flow.phase == "menu" and event.key == pygame.K_5:
                    flow.enter("settings")
                elif flow.phase == "attack" and event.key == pygame.K_m:
                    flow.enter("menu")
                elif flow.phase == "attack" and event.key == pygame.K_c:
                    flow.enter("characters")
                elif flow.phase == "characters" and event.key == pygame.K_1:
                    flow.character_slot = 0
                elif flow.phase == "characters" and event.key == pygame.K_2:
                    flow.character_slot = 1
                elif flow.phase == "characters" and event.key == pygame.K_ESCAPE:
                    flow.enter("menu")
                elif flow.phase == "settings" and event.key == pygame.K_ESCAPE:
                    flow.enter("menu")
                elif event.key == pygame.K_F11:
                    fullscreen = not fullscreen
                    if fullscreen:
                        pygame.display.set_mode((0, 0), pygame.FULLSCREEN)  # resolusi asli monitor
                    else:
                        pygame.display.set_mode((W, H), pygame.RESIZABLE)
                elif event.key == pygame.K_p:
                    projector = not projector
                elif event.key == pygame.K_v:
                    pov_mode = not pov_mode
                    if not pov_mode:
                        update_pov_window(None, None, False)
                    print(f"[POV] {'AKTIF' if pov_mode else 'NONAKTIF'} - jendela terpisah")
                elif event.key == pygame.K_SPACE and flow.phase == "dialogue" and (time.monotonic() - last_space_time) > 0.30:
                    last_space_time = time.monotonic()
                    # SPACE is only an explicit "continue" after the current
                    # voice has finished. It can never skip/cut a voice.
                    if audio.done():
                        scene = STORY["scenes"][flow.scene_index]
                        if flow.dialog_index < len(scene["dialogues"]) - 1:
                            flow.dialog_index += 1
                            play_dialogue()
                        elif flow.scene_index < len(STORY["scenes"]) - 1:
                            flow.scene_index += 1
                            print(f"[SCENE] Masuk adegan {STORY['scenes'][flow.scene_index]['id']}")
                            flow.enter("scene_transition")
                        else:
                            flow.enter("final_voice")
                elif flow.phase == "quiz" and event.key == pygame.K_m:
                    flow.enter("menu")
                elif flow.phase == "quiz" and event.key == pygame.K_ESCAPE:
                    flow.enter("menu")
                elif flow.phase == "quiz" and not flow.quiz_finished:
                    q = QUIZ_QUESTIONS[flow.quiz_index]
                    if flow.quiz_selected is not None and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if flow.quiz_selected == q["answer"]:
                            if flow.quiz_index < len(QUIZ_QUESTIONS) - 1:
                                flow.quiz_index += 1
                                flow.quiz_selected = None
                                flow.phase_started = time.monotonic()
                            else:
                                flow.quiz_finished = True
                                flow.phase_started = time.monotonic()
                        else:
                            flow.quiz_selected = None
                            flow.phase_started = time.monotonic()
                    elif flow.quiz_selected is None and event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                        choice = event.key - pygame.K_1
                        flow.quiz_selected = choice
                        if choice == q["answer"]:
                            flow.quiz_score += 1
                            print(f"[QUIZ] Soal {flow.quiz_index + 1}: BENAR")
                        else:
                            print(f"[QUIZ] Soal {flow.quiz_index + 1}: SALAH")
                        flow.phase_started = time.monotonic()

                # N intentionally does nothing now. The previous build could
                # accidentally skip narration/dialogue when N was pressed.

        # Hand tracking is isolated from the story flow so camera errors cannot
        # stop the story.
        if cam is not None and detector is not None:
            ok, frame = cam.read()
            camera_frame_counter += 1
            if ok and camera_frame_counter % 2 == 0:
                try:
                    frame = cv2.flip(frame, 1)
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    result = detector.process(rgb)
                    latest_hand_result = result
                    if pov_mode and flow.phase in ("attack", "scene_narration", "dialogue"):
                        update_pov_window(frame, result, True)
                    else:
                        update_pov_window(None, None, False)
                    hands = detect_hands(result, W, H)
                    left_hand = hands.get("Left")
                    right_hand = hands.get("Right")
                    unknown = hands.get("Unknown")
                    if flow.phase == "attack":
                        lh = left_hand or (unknown if not right_hand else None)
                        if lh:
                            gs = bima_gesture.update(lh["gesture"])
                            attack_left_state = gs
                            attack_left_puppet.update_hand(lh, float(puppet_cfg["smooth"]))
                            attack_left_puppet.set_visual_facing(1, CHARACTERS[flow.char_left_idx].get("source_facing", 1))
                            if gs == -1:
                                attack_left_puppet.target.x += 75
                        if right_hand:
                            gs = arjuna_gesture.update(right_hand["gesture"])
                            attack_right_state = gs
                            attack_right_puppet.update_hand(right_hand, float(puppet_cfg["smooth"]))
                            attack_right_puppet.set_visual_facing(-1, CHARACTERS[flow.char_right_idx].get("source_facing", 1))
                            if gs == -1:
                                attack_right_puppet.target.x -= 75
                    else:
                        if left_hand:
                            bima.update_hand(left_hand, float(puppet_cfg["smooth"]))
                            bima.set_facing(bima_gesture.update(left_hand["gesture"]))
                        elif unknown and not right_hand:
                            bima.update_hand(unknown, float(puppet_cfg["smooth"]))
                            bima.set_facing(bima_gesture.update(unknown["gesture"]))
                        if right_hand:
                            arjuna.update_hand(right_hand, float(puppet_cfg["smooth"]))
                            arjuna.set_facing(arjuna_gesture.update(right_hand["gesture"]))
                except Exception as exc:
                    print(f"[WARNING] Hand tracking dilewati: {exc}")
        
        # ---------------- FLOW ----------------
        if flow.phase == "menu":
            # Musik khusus menu: backsound gamelan berjalan loop dan tidak
            # mengganggu audio Story. Musik akan dimulai sekali saat menu aktif.
            if flow.settings_music and safe_sound_file("menu_gamelan.mp3"):
                if not pygame.mixer.music.get_busy() or not flow.menu_music_started:
                    pygame.mixer.music.load(str(AUDIO / "menu_gamelan.mp3"))
                    pygame.mixer.music.set_volume(0.26)
                    pygame.mixer.music.play(-1)
                    flow.menu_music_started = True
            elif not flow.settings_music and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                flow.menu_music_started = False
        elif flow.phase == "characters":
            if pygame.mixer.music.get_busy(): pygame.mixer.music.stop()
            flow.menu_music_started = False
        elif flow.phase == "settings":
            if pygame.mixer.music.get_busy(): pygame.mixer.music.stop()
            flow.menu_music_started = False
        elif flow.phase == "attack":
            flow.menu_music_started = False
            # Free-play mode: no story audio, no narration, no automatic scene changes.
            if flow.settings_music and not pygame.mixer.music.get_busy() and safe_sound_file("03_musik_pembuka.mp3"):
                pygame.mixer.music.load(str(AUDIO / "03_musik_pembuka.mp3")); pygame.mixer.music.set_volume(0.28); pygame.mixer.music.play(-1)
        elif flow.phase == "opening":
            if not flow.played:
                play_voice("01_pembukaan.mp3")
            if flow.played and audio.done():
                audio.stop()
                flow.enter("pause_after_opening")

        elif flow.phase == "pause_after_opening":
            if flow.elapsed() >= 1.0:
                flow.enter("after_pause_voice")

        elif flow.phase == "after_pause_voice":
            if not flow.played:
                play_voice("02_setelah_jeda.mp3")
            if flow.played and audio.done():
                audio.stop()
                if not flow.music_started and safe_sound_file("03_musik_pembuka.mp3"):
                    pygame.mixer.music.load(str(AUDIO / "03_musik_pembuka.mp3"))
                    pygame.mixer.music.set_volume(0.0)
                    pygame.mixer.music.play(-1)
                    flow.music_started = True
                flow.enter("mari")

        elif flow.phase == "mari":
            if flow.music_started:
                pygame.mixer.music.set_volume(min(0.50, flow.elapsed() / 2.5 * 0.50))
            if not flow.played:
                play_voice("04_mari_kita_ikuti.mp3")
            if flow.played and audio.done():
                audio.stop()
                flow.enter("title_fade")
                flow.title_started = time.monotonic()

        elif flow.phase == "title_fade":
            # Darken the scene first; title enters softly during the darkening.
            duration = 2.8
            if flow.elapsed() >= duration:
                flow.enter("title_voice_1")

        elif flow.phase == "title_voice_1":
            if not flow.played:
                play_voice("05_judul_subjudul.mp3")
            if flow.played and audio.done():
                audio.stop()
                flow.enter("title_voice_2")

        elif flow.phase == "title_voice_2":
            if not flow.played:
                play_voice("06_judul_utama.mp3")
            if flow.played and audio.done():
                audio.stop()
                flow.enter("title_hold")

        elif flow.phase == "title_hold":
            if flow.elapsed() >= 2.0:
                if flow.music_started:
                    pygame.mixer.music.fadeout(1400)
                flow.enter("scene_narration")

        elif flow.phase == "scene_transition":
            # The previous voice has already finished before this phase is
            # entered. Keep a short visual transition, then start the next
            # scene narration. Never play/cut audio during the transition.
            if flow.elapsed() >= 0.65:
                flow.enter("scene_narration")

        elif flow.phase == "scene_narration":
            if not flow.played:
                start_scene_narration()
            # Use the measured Sound length as the authoritative end point.
            # This prevents a mixer/channel timing race from advancing early.
            narration_done = audio.done()
            if narration_done:
                audio.stop()
                # Give the last narration frame a brief visual hold before the
                # first character voice. This prevents the narration and first
                # dialogue from visually colliding at the boundary.
                flow.dialog_index = 0
                flow.enter("dialogue_start")

        elif flow.phase == "dialogue_start":
            if flow.elapsed() >= 0.28:
                flow.enter("dialogue")
                play_dialogue()

        elif flow.phase == "dialogue":
            scene = STORY["scenes"][flow.scene_index]
            # Each dialogue waits for its own measured audio length. We do not
            # use the old fixed 5.5-second setting.
            dialogue_done = flow.played and audio.done()
            if dialogue_done:
                audio.stop()
                if flow.dialog_index < len(scene["dialogues"]) - 1:
                    flow.dialog_index += 1
                    play_dialogue()
                elif flow.scene_index < len(STORY["scenes"]) - 1:
                    flow.scene_index += 1
                    print(f"[SCENE] Masuk adegan {STORY['scenes'][flow.scene_index]['id']}")
                    flow.enter("scene_transition")
                else:
                    flow.enter("final_voice")

        elif flow.phase == "final_voice":
            if not flow.played:
                play_voice("12_akhir_cerita.mp3")
            if flow.played and audio.done():
                audio.stop()
                flow.enter("moral_pause")

        elif flow.phase == "moral_pause":
            if flow.elapsed() >= 1.2:
                flow.enter("moral")

        elif flow.phase == "moral":
            if not flow.played:
                play_voice("13_pesan_moral.mp3")
            if flow.played and audio.done():
                audio.stop()
                flow.enter("closing_voice")

        elif flow.phase == "closing_voice":
            if not flow.played:
                play_voice("14_penutup.mp3")
            if flow.played and audio.done():
                audio.stop()
                flow.enter("ending")

        elif flow.phase == "ending":
            if flow.elapsed() >= 8.0:
                flow.enter("quiz")
                flow.quiz_index = 0
                flow.quiz_score = 0
                flow.quiz_selected = None
                flow.quiz_finished = False
                print("[QUIZ] Mulai kuis penonton")

        elif flow.phase == "quiz":
            # Feedback popup stays open until the user chooses Lanjut/Ulangi.
            pass

        # ---------------- DRAW ----------------
        if flow.phase == "menu":
            mouse_x, mouse_y = logical_mouse()
            hover = next((key for key, r in menu_button_layout(W, H) if r.collidepoint(mouse_x, mouse_y)), None)
            draw_menu(screen, backgrounds, W, H, big_font, sub_font, text_font, small_font, hover)
        elif flow.phase == "characters":
            draw_character_menu(screen, backgrounds, W, H, big_font, sub_font, text_font, small_font, flow.char_left_idx, flow.char_right_idx, flow.character_slot)
        elif flow.phase == "settings":
            draw_settings(screen, backgrounds, W, H, big_font, text_font, small_font, pov_mode, flow.settings_music)
        elif flow.phase == "attack":
            draw_attack(screen, backgrounds, W, H, big_font, text_font, small_font, attack_left_puppet, attack_right_puppet, CHARACTERS[flow.char_left_idx]["name"], CHARACTERS[flow.char_right_idx]["name"], attack_left_state == -1, attack_right_state == -1)
        elif flow.phase in ("opening", "pause_after_opening", "after_pause_voice", "mari", "title_fade", "title_voice_1", "title_voice_2", "title_hold", "scene_transition"):
            transition_bg = "hutan_sore"
            if flow.phase == "scene_transition" and 0 <= flow.scene_index < len(STORY["scenes"]):
                transition_bg = STORY["scenes"][flow.scene_index]["background"]
            draw_background(screen, backgrounds, transition_bg, W, H)
            if flow.phase not in ("title_fade", "title_voice_1", "title_voice_2", "title_hold"):
                bima.draw_at(screen, (410, 470), 0.82)
                arjuna.draw_at(screen, (870, 470), 0.82)
            if flow.phase == "opening":
                opening_text, opening_alpha, _ = opening_text_for_current_time()
                # Gambar subtitle pembukaan langsung; tidak menjalankan lagi
                # sentence scheduler di dalam draw_narration.
                panel_h = 165
                panel = pygame.Surface((W - 100, panel_h), pygame.SRCALPHA)
                panel.fill((0, 0, 0, int(190 * max(0.82, opening_alpha / 255))))
                screen.blit(panel, (50, H - panel_h - 25))
                label = pygame.font.SysFont("Arial", 28, bold=True).render("Narator", True, (255, 235, 170))
                label.set_alpha(opening_alpha)
                screen.blit(label, (80, H - panel_h - 8))
                y = H - panel_h + 36
                for line in wrap_text(text_font, opening_text, W - 160)[:3]:
                    surf = text_font.render(line, True, (255, 255, 255))
                    surf.set_alpha(opening_alpha)
                    screen.blit(surf, (80, y))
                    y += 32
            elif flow.phase == "after_pause_voice":
                draw_narration(screen, AFTER_PAUSE_TEXT, W, H, text_font, audio.elapsed(), audio.current_length, "Narator", audio.current_lead, audio.current_tail)
            elif flow.phase in ("title_fade", "title_voice_1", "title_voice_2", "title_hold"):
                p = min(1.0, flow.elapsed() / 2.8) if flow.phase == "title_fade" else 1.0
                fade_overlay(screen, W, H, 235 * p)
                draw_title(screen, W, H, big_font, sub_font, p)

        elif flow.phase in ("scene_narration", "dialogue_start", "dialogue"):
            scene = STORY["scenes"][flow.scene_index]
            draw_background(screen, backgrounds, scene["background"], W, H)
            bima.draw(screen)
            arjuna.draw(screen)
            if flow.phase == "scene_narration":
                draw_narration(screen, scene.get("narration_text", ""), W, H, text_font, audio.elapsed(), audio.current_length, "Narator", audio.current_lead, audio.current_tail, NARRATION_TIMINGS.get(scene.get("narration")))
            elif flow.phase == "dialogue_start":
                # Keep the final narration frame visible during the short
                # handoff instead of flashing an empty panel.
                last_sentence = split_sentences(scene.get("narration_text", ""))[-1:]
                draw_narration(screen, " ".join(last_sentence), W, H, text_font, 1.0, 1.0, "Narator", 0.0, 0.0)
            else:
                speaker, text, _ = scene["dialogues"][flow.dialog_index]
                draw_dialogue(screen, speaker, text, W, H, speaker_font, text_font, audio.elapsed(), audio.current_length, audio.current_lead, audio.current_tail)

        elif flow.phase in ("final_voice", "moral_pause", "moral", "closing_voice"):
            draw_background(screen, backgrounds, "hutan_sore", W, H)
            bima.draw(screen)
            arjuna.draw(screen)
            if flow.phase == "final_voice":
                draw_narration(screen, FINAL_STORY_TEXT, W, H, text_font, audio.elapsed(), audio.current_length, "Narator", audio.current_lead, audio.current_tail, NARRATION_TIMINGS.get("12_akhir_cerita.mp3"))
            elif flow.phase == "moral":
                draw_narration(screen, MORAL_TEXT, W, H, text_font, audio.elapsed(), audio.current_length, "Pesan Moral", audio.current_lead, audio.current_tail, NARRATION_TIMINGS.get("13_pesan_moral.mp3"))
            elif flow.phase == "closing_voice":
                draw_narration(screen, CLOSING_TEXT, W, H, text_font, audio.elapsed(), audio.current_length, "Penutup", audio.current_lead, audio.current_tail, NARRATION_TIMINGS.get("14_penutup.mp3"))

        elif flow.phase == "ending":
            draw_background(screen, backgrounds, "hutan_sore", W, H)
            t = min(1.0, flow.elapsed() / 6.0)
            scale = 1.0 - 0.78 * t
            y = 455 - 100 * t
            x1 = 370 + 175 * t
            x2 = 910 - 175 * t
            bima.draw_at(screen, (x1, y), scale)
            arjuna.draw_at(screen, (x2, y), scale)
            if not flow.music_started:
                if safe_sound_file("03_musik_pembuka.mp3"):
                    pygame.mixer.music.load(str(AUDIO / "03_musik_pembuka.mp3"))
                    pygame.mixer.music.set_volume(0.35)
                    pygame.mixer.music.play(-1)
                flow.music_started = True
            if t > 0.55:
                pygame.mixer.music.set_volume(max(0, 0.35 - (t - 0.55) * 0.7))
            if t > 0.70:
                fade_overlay(screen, W, H, (t - 0.70) / 0.30 * 255)
            if t > 0.90:
                alpha = int(min(255, (t - 0.90) / 0.10 * 255))
                msg = text_font.render(ENDING_TEXT, True, (255, 255, 255))
                msg.set_alpha(alpha)
                screen.blit(msg, msg.get_rect(center=(W // 2, H // 2)))
                tamat = sub_font.render("TAMAT", True, (255, 245, 210))
                tamat.set_alpha(alpha)
                screen.blit(tamat, tamat.get_rect(center=(W // 2, H // 2 + 70)))

        elif flow.phase == "quiz":
            draw_quiz_ui(
                screen, backgrounds, W, H, big_font, sub_font, text_font, small_font,
                flow.quiz_index, flow.quiz_score, flow.quiz_selected, flow.quiz_finished
            )

        elif flow.phase == "done":
            screen.fill((0, 0, 0))
            msg = sub_font.render("TAMAT", True, (255, 255, 255))
            screen.blit(msg, msg.get_rect(center=(W // 2, H // 2)))

        if not projector and flow.phase in ("scene_narration", "dialogue"):
            hint = small_font.render(
                "✊ mengepal = kiri | 🖐 telapak = kanan | SPACE = lanjut setelah suara selesai | V = buka/tutup jendela POV | F11 = fullscreen | ESC = keluar",
                True, (255, 255, 255),
            )
            screen.blit(hint, (18, 18))

        present_canvas(screen)
        clock.tick(30)

    audio.stop()
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass
    if detector is not None:
        detector.close()
    if cam is not None:
        cam.release()
    try:
        cv2.destroyWindow("POV Tangan - Live")
        cv2.destroyAllWindows()
    except Exception:
        pass
    pygame.quit()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        print("\nProgram berhenti karena error. Tekan ENTER untuk menutup terminal.")
        try:
            input()
        except EOFError:
            pass
