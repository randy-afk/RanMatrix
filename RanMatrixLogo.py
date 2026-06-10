#!/usr/bin/env python3
"""
RanMatrixLogo.py
------------------
Generates RanMatrix logo assets:
  logo_gui.png  — 200×50px  (title bar, about dialog)
  logo_docs.png — 600×150px (splash, docs)

Run standalone:  python RanMatrixLogo.py
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
from pathlib import Path

# ── Palette (RanOptics) ────────────────────────────────────────────────────
BG      = "#2C5446"
PANEL   = "#234438"
ACCENT  = "#FDA769"
FG      = "#EEF5F2"
FG_DIM  = "#A8C4BC"
TWISS_A = "#74c0fc"
TWISS_B = "#69db7c"
BORDER  = "#5A8A78"
CRUST   = "#192E26"


def _draw_logo(ax_matrix, ax_ellipse, ax_text, scale: float = 1.0):
    """Draw all logo elements into the given axes."""

    # ── Mini 6×6 matrix grid ──────────────────────────────────────────────
    n = 6
    cell = 0.14 * scale
    origin_x, origin_y = 0.05 * scale, 0.1 * scale

    # Simulated FODO one-turn matrix values (realistic, not identity)
    M = np.array([
        [-0.45,  3.80,  0.00,  0.00,  0.00,  0.05],
        [-0.48,  1.82,  0.00,  0.00,  0.00,  0.00],
        [ 0.00,  0.00,  0.62,  2.14,  0.00,  0.00],
        [ 0.00,  0.00, -0.31,  0.62,  0.00,  0.00],
        [ 0.00,  0.00,  0.00,  0.00,  1.00, -3.00],
        [ 0.00,  0.00,  0.00,  0.00,  0.00,  1.00],
    ])
    max_abs = np.abs(M).max()

    for r in range(n):
        for c in range(n):
            v = M[r, c]
            frac = abs(v) / max_abs
            # interpolate PANEL → ACCENT
            ri = int(0x23 + frac * (0xFD - 0x23))
            gi = int(0x44 + frac * (0xA7 - 0x44))
            bi = int(0x38 + frac * (0x69 - 0x38))
            color = f"#{ri:02x}{gi:02x}{bi:02x}"

            rect = plt.Rectangle(
                (origin_x + c * cell, origin_y + (n - 1 - r) * cell),
                cell * 0.88, cell * 0.88,
                facecolor=color, edgecolor=BORDER,
                linewidth=0.3 * scale, zorder=2
            )
            ax_matrix.add_patch(rect)

    ax_matrix.set_xlim(0, n * cell + origin_x * 2)
    ax_matrix.set_ylim(0, n * cell + origin_y * 2)
    ax_matrix.set_aspect("equal")
    ax_matrix.axis("off")

    # ── Phase space ellipse ───────────────────────────────────────────────
    phi = np.linspace(0, 2 * np.pi, 200)
    # Tilted ellipse (nonzero alpha)
    beta, alpha, eps = 3.5, -1.2, 1.0
    gamma = (1 + alpha**2) / beta
    x  = np.sqrt(eps * beta) * np.cos(phi)
    xp = -np.sqrt(eps / beta) * (alpha * np.cos(phi) + np.sin(phi))

    # Normalise to unit box
    x  = x  / np.max(np.abs(x))
    xp = xp / np.max(np.abs(xp))

    ax_ellipse.plot(x * 0.42, xp * 0.42,
                    color=TWISS_A, lw=1.8 * scale, zorder=3)

    # Ghost ellipses
    for s_frac in [0.25, 0.55]:
        beta_s  = beta  * (1 - s_frac * 0.6)
        alpha_s = alpha * (1 - s_frac * 1.2)
        gamma_s = (1 + alpha_s**2) / beta_s
        xs  = np.sqrt(eps * beta_s) * np.cos(phi)
        xps = -np.sqrt(eps / beta_s) * (alpha_s * np.cos(phi) + np.sin(phi))
        xs  = xs  / np.max(np.abs(xs))
        xps = xps / np.max(np.abs(xps))
        ax_ellipse.plot(xs * 0.42, xps * 0.42,
                        color=BORDER, lw=0.7 * scale, alpha=0.5,
                        ls="--", zorder=2)

    # Entrance ellipse (orange)
    beta_e, alpha_e = 5.0, 0.0
    xe  = np.sqrt(eps * beta_e) * np.cos(phi)
    xpe = -np.sqrt(eps / beta_e) * (alpha_e * np.cos(phi) + np.sin(phi))
    xe  = xe  / np.max(np.abs(xe))
    xpe = xpe / np.max(np.abs(xpe))
    ax_ellipse.plot(xe * 0.42, xpe * 0.42,
                    color=ACCENT, lw=1.2 * scale, ls="--",
                    alpha=0.85, zorder=3)

    # Axes lines
    ax_ellipse.axhline(0, color=BORDER, lw=0.5 * scale, alpha=0.5)
    ax_ellipse.axvline(0, color=BORDER, lw=0.5 * scale, alpha=0.5)
    ax_ellipse.set_xlim(-0.55, 0.55)
    ax_ellipse.set_ylim(-0.55, 0.55)
    ax_ellipse.set_aspect("equal")
    ax_ellipse.axis("off")


def make_logo(width_px: int, height_px: int,
              dpi: int, out_path: Path):
    """Generate one logo PNG."""
    w_in = width_px  / dpi
    h_in = height_px / dpi
    scale = h_in * 1.8   # scale elements to figure height

    fig = plt.figure(figsize=(w_in, h_in), facecolor=CRUST)

    # Layout: [matrix | ellipse | wordmark]
    # proportions: 0.22 | 0.22 | 0.56
    ax_m = fig.add_axes([0.02, 0.05, 0.22, 0.90])
    ax_m.set_facecolor(CRUST)
    ax_e = fig.add_axes([0.24, 0.05, 0.22, 0.90])
    ax_e.set_facecolor(CRUST)
    ax_t = fig.add_axes([0.46, 0.00, 0.54, 1.00])
    ax_t.set_facecolor(CRUST)
    ax_t.axis("off")

    _draw_logo(ax_m, ax_e, ax_t, scale=scale)

    # Wordmark
    ax_t.text(0.02, 0.65, "RanMatrix",
              color=FG,
              fontsize=max(7, int(18 * scale)),
              fontweight="bold",
              fontfamily="monospace",
              va="center", ha="left",
              transform=ax_t.transAxes)

    ax_t.text(0.02, 0.28, "v1.0.0  |  Beam Optics Explorer",
              color=FG_DIM,
              fontsize=max(5, int(8 * scale)),
              fontfamily="sans-serif",
              va="center", ha="left",
              transform=ax_t.transAxes)

    # Accent bar under wordmark
    from matplotlib.lines import Line2D
    line = Line2D([0.02, 0.87], [0.48, 0.48],
                  transform=ax_t.transAxes,
                  color=ACCENT, lw=max(0.8, 1.5 * scale))
    ax_t.add_line(line)

    fig.savefig(out_path, dpi=dpi, bbox_inches="tight",
                facecolor=CRUST, pad_inches=0.01)
    plt.close(fig)
    print(f"  Saved: {out_path}  ({width_px}×{height_px}px)")


if __name__ == "__main__":
    out_dir = Path(__file__).parent / "assets"
    out_dir.mkdir(exist_ok=True)

    print("Generating RanMatrix logo assets...")
    make_logo(200,  50,  100, out_dir / "logo_gui.png")
    make_logo(600, 150,  150, out_dir / "logo_docs.png")
    print("Done.")
