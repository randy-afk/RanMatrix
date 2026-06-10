"""
gui/step_mode.py
----------------
Step mode animation controller.

Shows element-by-element progression:
  - Current element block highlighted in lattice line
  - Element R matrix displayed
  - Cumulative R matrix displayed
  - Phase space ellipse morphing step by step
  - Play / Pause / Step Forward / Step Back / Reset controls
"""

from __future__ import annotations
import numpy as np
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QFrame, QSizePolicy
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

import theme
from models.lattice import LatticeResult
from physics.matrices import (
    ellipse_points, propagate_twiss, propagate_particle
)


def _btn(text: str, accent: bool = False) -> QPushButton:
    b = QPushButton(text)
    b.setFixedHeight(28)
    if accent:
        b.setProperty("accent", "true")
    return b


def _sep() -> QFrame:
    f = QFrame(); f.setFrameShape(QFrame.VLine)
    f.setStyleSheet(f"color:{theme.BORDER};")
    return f


class StepModePanel(QWidget):
    """
    Full step-mode controller + mini phase-space canvas.
    Exposed signal: step_changed(int) — emitted whenever the current
    step index changes, so main_window can highlight the block.
    """

    step_changed = Signal(int)    # current element index (0-based)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._result: LatticeResult | None = None
        self._step    = 0         # current element index (0 = before first element)
        self._playing = False
        self._interval_ms = 600   # animation interval

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._auto_step)

        theme.apply_mpl_theme()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(6)

        # ── Transport controls ─────────────────────────────────────
        ctrl = QHBoxLayout()
        ctrl.setSpacing(4)

        self._btn_reset = _btn("⏮  Reset")
        self._btn_back  = _btn("◀  Back")
        self._btn_play  = _btn("▶  Play", accent=True)
        self._btn_fwd   = _btn("▶|  Step")
        self._btn_end   = _btn("⏭  End")

        self._btn_reset.clicked.connect(self._on_reset)
        self._btn_back.clicked.connect(self._on_back)
        self._btn_play.clicked.connect(self._on_play_pause)
        self._btn_fwd.clicked.connect(self._on_forward)
        self._btn_end.clicked.connect(self._on_end)

        # Speed slider
        spd_lbl = QLabel("Speed:")
        spd_lbl.setStyleSheet(
            f"color:{theme.FG_LBL}; font-size:{theme.FONT_TINY}px;")
        self._spd_slider = QSlider(Qt.Horizontal)
        self._spd_slider.setRange(1, 10)
        self._spd_slider.setValue(5)
        self._spd_slider.setFixedWidth(80)
        self._spd_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background:{theme.MANTLE}; height:4px; border-radius:2px;}}
            QSlider::handle:horizontal {{
                background:{theme.ACCENT}; width:12px; height:12px;
                margin:-4px 0; border-radius:6px;}}
            QSlider::sub-page:horizontal {{
                background:{theme.ACCENT}; border-radius:2px;}}
        """)
        self._spd_slider.valueChanged.connect(self._on_speed_changed)

        for w in [self._btn_reset, self._btn_back, _sep(),
                  self._btn_play, _sep(),
                  self._btn_fwd, self._btn_end,
                  _sep(), spd_lbl, self._spd_slider]:
            ctrl.addWidget(w)
        ctrl.addStretch()
        lay.addLayout(ctrl)

        # ── Step info bar ──────────────────────────────────────────
        self._info_lbl = QLabel("No lattice loaded")
        self._info_lbl.setStyleSheet(
            f"color:{theme.ACCENT}; font-size:{theme.FONT_SMALL}px; "
            f"font-weight:bold; background:transparent;")
        lay.addWidget(self._info_lbl)

        # ── Mini matrix display ────────────────────────────────────
        mat_row = QHBoxLayout()
        mat_row.setSpacing(10)

        self._mat_elem_lbl  = self._make_matrix_label("Element R")
        self._mat_cumul_lbl = self._make_matrix_label("Cumulative R")
        mat_row.addWidget(self._mat_elem_lbl[0])
        mat_row.addWidget(self._mat_cumul_lbl[0])
        mat_row.addStretch()
        lay.addLayout(mat_row)

        # ── Phase space canvas ─────────────────────────────────────
        self._fig = Figure(figsize=(6, 3.0), facecolor=theme.BG)
        self._canvas = FigureCanvasQTAgg(self._fig)
        self._ax = self._fig.add_subplot(111)
        self._fig.subplots_adjust(
            left=0.10, right=0.97, top=0.93, bottom=0.13)
        lay.addWidget(self._canvas, 1)

        self._draw_empty()
        self._update_controls()

    # ── Public API ────────────────────────────────────────────────

    def update_result(self, result: LatticeResult):
        self._result = result
        self._step   = 0
        self._playing = False
        self._timer.stop()
        self._btn_play.setText("▶  Play")
        self._update_all()

    # ── Controls ──────────────────────────────────────────────────

    def _on_reset(self):
        self._step = 0
        self._playing = False
        self._timer.stop()
        self._btn_play.setText("▶  Play")
        self._update_all()

    def _on_back(self):
        if self._step > 0:
            self._step -= 1
            self._update_all()

    def _on_forward(self):
        if self._result and self._step < self._result.n_elements:
            self._step += 1
            self._update_all()

    def _on_end(self):
        if self._result:
            self._step = self._result.n_elements
            self._update_all()

    def _on_play_pause(self):
        if not self._result:
            return
        self._playing = not self._playing
        if self._playing:
            self._btn_play.setText("⏸  Pause")
            self._timer.start(self._interval_ms)
        else:
            self._btn_play.setText("▶  Play")
            self._timer.stop()

    def _auto_step(self):
        if self._result and self._step < self._result.n_elements:
            self._step += 1
            self._update_all()
        else:
            self._playing = False
            self._timer.stop()
            self._btn_play.setText("▶  Play")

    def _on_speed_changed(self, v: int):
        # v: 1 (slow) → 10 (fast) → interval 1200ms → 120ms
        self._interval_ms = int(1200 / v)
        if self._playing:
            self._timer.setInterval(self._interval_ms)

    # ── Update helpers ────────────────────────────────────────────

    def _update_all(self):
        self._update_info()
        self._update_matrices()
        self._update_canvas()
        self._update_controls()
        # Emit to highlight block in lattice line
        if self._result and 0 < self._step <= self._result.n_elements:
            self.step_changed.emit(self._step - 1)

    def _update_info(self):
        r = self._result
        if r is None:
            self._info_lbl.setText("No lattice loaded")
            return
        n = r.n_elements
        if self._step == 0:
            self._info_lbl.setText(
                f"Step 0 / {n}  —  Entrance  (s = 0.00 m)")
        elif self._step <= n:
            elems = getattr(r, '_elements', None)
            s_val = r.s_positions[self._step]
            name  = (elems[self._step - 1].label
                     if elems else f"Element {self._step}")
            etype = (elems[self._step - 1].etype.value
                     if elems else "")
            tp    = r.twiss_points[self._step]
            self._info_lbl.setText(
                f"Step {self._step} / {n}  —  {name}  ({etype})  "
                f"s = {s_val:.3f} m   "
                f"βx = {tp.betax:.3f} m   βy = {tp.betay:.3f} m")

    def _update_matrices(self):
        r = self._result
        if r is None or self._step == 0:
            self._mat_elem_lbl[1].setText("—")
            self._mat_cumul_lbl[1].setText("—")
            return
        idx = self._step - 1
        if idx >= len(r.R_each):
            return
        self._mat_elem_lbl[1].setText(
            self._fmt_matrix_compact(r.R_each[idx]))
        self._mat_cumul_lbl[1].setText(
            self._fmt_matrix_compact(r.R_cumul[self._step]))

    def _fmt_matrix_compact(self, M: np.ndarray) -> str:
        """Format 6×6 matrix as compact monospace string (x-plane only for brevity)."""
        lines = ["x-plane:"]
        m2 = M[:2, :2]
        for row in m2:
            lines.append(f"  [{row[0]:+.4f}  {row[1]:+.4f}]")
        lines.append(f"R₁₆={M[0,5]:+.4f}  R₅₆={M[4,5]:+.4f}")
        return "\n".join(lines)

    def _update_controls(self):
        r = self._result
        n = r.n_elements if r else 0
        self._btn_back.setEnabled(self._step > 0)
        self._btn_fwd.setEnabled(self._step < n)
        self._btn_end.setEnabled(self._step < n)
        self._btn_reset.setEnabled(self._step > 0)
        self._btn_play.setEnabled(n > 0)

    def _update_canvas(self):
        r = self._result
        if r is None:
            self._draw_empty()
            return

        ax = self._ax; ax.cla()
        ax.set_facecolor(theme.PANEL)
        ax.set_xlabel("x  (mm)", color=theme.FG_LBL,
                      fontsize=theme.FONT_SMALL)
        ax.set_ylabel("x'  (mrad)", color=theme.FG_LBL,
                      fontsize=theme.FONT_SMALL)
        ax.set_title("Phase Space — step mode  (x, x')",
                     color=theme.FG, fontsize=theme.FONT_SMALL)
        ax.tick_params(colors=theme.FG_LBL, labelsize=theme.FONT_TINY)
        for sp in ax.spines.values():
            sp.set_edgecolor(theme.BORDER)
        ax.axhline(0, color=theme.BORDER, lw=0.5, ls="--")
        ax.axvline(0, color=theme.BORDER, lw=0.5, ls="--")

        tp0   = r.twiss_points[0]
        eps   = 1e-6
        beta0 = tp0.betax; alpha0 = tp0.alphax

        # Entrance ellipse (always shown)
        ei, eip = ellipse_points(eps, beta0, alpha0)
        ax.plot(ei*1e3, eip*1e3, color=theme.ACCENT,
                lw=1.2, ls="--", alpha=0.6,
                label="Entrance")

        # All previous boundaries as dim ghosts
        for k in range(1, self._step):
            tp_k = r.twiss_points[k]
            b, a = tp_k.betax, tp_k.alphax
            if b > 0:
                gx, gxp = ellipse_points(eps, b, a)
                ax.plot(gx*1e3, gxp*1e3, color=theme.COLOR_GHOST,
                        lw=0.5, alpha=0.2, ls="--", zorder=1)

        # Current ellipse — highlighted
        tp_cur = r.twiss_points[self._step]
        b_cur  = tp_cur.betax; a_cur = tp_cur.alphax
        if b_cur > 0:
            cx, cxp = ellipse_points(eps, b_cur, a_cur)
            elems = getattr(r, '_elements', None)
            if self._step > 0 and elems:
                col = elems[self._step - 1].color
            else:
                col = theme.TWISS_A
            ax.plot(cx*1e3, cxp*1e3, color=col,
                    lw=2.5, zorder=4,
                    label=f"Step {self._step}")

        # Particle trajectory up to current step
        traj = propagate_particle(
            1e-3, 0.0, 0.0, 0.0,
            r.R_each[:self._step])
        xs  = [v*1e3 for v in traj["x"]]
        xps = [v*1e3 for v in traj["xp"]]
        ax.plot(xs, xps, "o-", color=theme.COLOR_PARTICLE,
                ms=5, lw=1.3, zorder=5, label="Particle")
        if xs:
            ax.plot(xs[-1], xps[-1], "*",
                    color=theme.COLOR_PARTICLE, ms=10, zorder=6)

        ax.legend(fontsize=theme.FONT_TINY, framealpha=0.3,
                  facecolor=theme.PANEL, edgecolor=theme.BORDER,
                  labelcolor=theme.FG)
        ax.grid(True, color=theme.BORDER, alpha=0.25, ls="--")
        self._canvas.draw()

    # ── Helpers ───────────────────────────────────────────────────

    def _draw_empty(self):
        ax = self._ax; ax.cla()
        ax.set_facecolor(theme.PANEL)
        for sp in ax.spines.values():
            sp.set_edgecolor(theme.BORDER)
        ax.text(0.5, 0.5, "Step mode — load a lattice to begin",
                transform=ax.transAxes, color=theme.FG_LBL,
                ha="center", va="center", fontsize=theme.FONT_BODY)
        self._canvas.draw()

    def _make_matrix_label(self, title: str):
        """Returns (container_widget, text_label)."""
        w = QWidget()
        w.setStyleSheet(
            f"background:{theme.MANTLE}; border-radius:4px;")
        lay = QVBoxLayout(w); lay.setContentsMargins(6, 4, 6, 4)
        lay.setSpacing(2)
        hdr = QLabel(title)
        hdr.setStyleSheet(
            f"color:{theme.ACCENT}; font-size:{theme.FONT_TINY}px; "
            f"font-weight:bold; background:transparent;")
        val = QLabel("—")
        val.setStyleSheet(
            f"color:{theme.FG}; font-size:{theme.FONT_TINY}px; "
            f"font-family:monospace; background:transparent;")
        lay.addWidget(hdr); lay.addWidget(val)
        return w, val
