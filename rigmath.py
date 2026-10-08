"""Matematika rig wayang (tanpa pygame supaya mudah diuji)."""
import math


def solve_arm(target, lu, lf, bend=1):
    """IK dua tulang. target = (dx, dy) relatif terhadap bahu (koordinat gambar, y ke bawah).
    Mengembalikan (theta_upper, theta_fore, elbow_vec, hand_vec); sudut dalam radian."""
    tx, ty = target
    d = math.hypot(tx, ty)
    d = max(min(d, lu + lf - 1e-3), abs(lu - lf) + 1e-3)
    base = math.atan2(ty, tx)
    cos_a = (lu * lu + d * d - lf * lf) / (2.0 * lu * d)
    a = math.acos(max(-1.0, min(1.0, cos_a)))
    th_u = base - a * bend
    ex, ey = lu * math.cos(th_u), lu * math.sin(th_u)
    hx, hy = d * math.cos(base), d * math.sin(base)
    th_f = math.atan2(hy - ey, hx - ex)
    return th_u, th_f, (ex, ey), (hx, hy)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def arm_target_from_hand(v, flip, lu, lf, lo, hi, min_frac=0.35):
    """v = vektor layar (ujung jari - pergelangan) / ukuran telapak.
    Hasil: vektor target lengan di ruang lokal gambar (sudah dicerminkan jika flip)."""
    vx, vy = v
    length = math.hypot(vx, vy)
    if length < 1e-6:
        return None
    k = clamp((length - lo) / max(1e-6, hi - lo), min_frac, 1.0)
    reach = (lu + lf) * 0.98 * k
    lx = vx * (-1 if flip else 1)
    n = math.hypot(lx, vy)
    return (lx / n * reach, vy / n * reach)
