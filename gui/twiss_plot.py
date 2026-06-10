"""
gui/twiss_plot.py
-----------------
Twiss function plot: βx(s), βy(s), αx(s), αy(s), Dx(s), Dy(s)
along the lattice with element bar at the top.

Clicking on the element bar highlights that element.
"""

from __future__ import annotations
import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QComboBox
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
import matplotlib.ticker as ticker

import theme
from models.lattice import LatticeResult


class TwissPlotPanel(QWidget):
    """βx(s), βy(s) + optional αx, αy, Dx, Dy plotted along s."""

    element_selected = Signal(str)   # uid when user clicks element bar

    def __init__(self, parent=None):
        super().__init__(parent)
        self._result: LatticeResult | None = None
        theme.apply_mpl_theme()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(4)

        # Controls
        ctrl = QHBoxLayout()
        ctrl.setSpacing(10)

        def _cb(label, checked=True):
            cb = QCheckBox(label)
            cb.setChecked(checked)
            cb.setStyleSheet(
                f"color:{theme.FG_DIM}; font-size:{theme.FONT_TINY}px;")
            cb.toggled.connect(self._redraw)
            return cb

        self._cb_bx   = _cb("βx",  True)
        self._cb_by   = _cb("βy",  True)
        self._cb_ax   = _cb("αx",  False)
        self._cb_ay   = _cb("αy",  False)
        self._cb_dx   = _cb("Dx",  True)
        self._cb_dy   = _cb("Dy",  False)
        self._cb_elem = _cb("Element bar", True)

        for w in [self._cb_bx, self._cb_by, self._cb_ax,
                  self._cb_ay, self._cb_dx, self._cb_dy,
                  self._cb_elem]:
            ctrl.addWidget(w)

        # Δp/p slider
        from PySide6.QtWidgets import QSlider
        dp_lbl = QLabel("  Δp/p:")
        dp_lbl.setStyleSheet(
            f"color:{theme.FG_LBL}; font-size:{theme.FONT_TINY}px;")
        self._dp_slider = QSlider(Qt.Horizontal)
        self._dp_slider.setRange(-100, 100)
        self._dp_slider.setValue(0)
        self._dp_slider.setFixedWidth(100)
        self._dp_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background:{theme.MANTLE}; height:4px; border-radius:2px;}}
            QSlider::handle:horizontal {{
                background:{theme.ACCENT}; width:12px; height:12px;
                margin:-4px 0; border-radius:6px;}}
            QSlider::sub-page:horizontal {{
                background:{theme.ACCENT}; border-radius:2px;}}
        """)
        self._dp_val = QLabel("0.00%")
        self._dp_val.setStyleSheet(
            f"color:{theme.FG}; font-size:{theme.FONT_TINY}px; min-width:45px;")
        self._dp_slider.valueChanged.connect(self._on_dp_changed)
        ctrl.addWidget(dp_lbl)
        ctrl.addWidget(self._dp_slider)
        ctrl.addWidget(self._dp_val)

        ctrl.addStretch()
        lay.addLayout(ctrl)

        self._delta_p = 0.0

        # Canvas — two subplots: Twiss top, Dispersion bottom
        self._fig = Figure(figsize=(7, 4.5), facecolor=theme.BG)
        self._canvas = FigureCanvasQTAgg(self._fig)
        self._fig.canvas.mpl_connect("button_press_event", self._on_click)
        lay.addWidget(self._canvas, 1)

        self._delta_p = 0.0
        self._draw_empty()

    def _on_dp_changed(self, v: int):
        self._delta_p = v / 1000.0
        self._dp_val.setText(f"{self._delta_p*100:+.2f}%")
        self._redraw()

    # ── Public API ────────────────────────────────────────────────

    def update_result(self, result: LatticeResult):
        self._result = result
        self._redraw()

    def highlight_element(self, uid: str | None, idx: int | None):
        """Called from outside — re-render with highlight."""
        self._highlighted_idx = idx
        self._redraw()

    # ── Drawing ───────────────────────────────────────────────────

    def _draw_empty(self):
        self._fig.clear()
        ax = self._fig.add_subplot(111)
        ax.set_facecolor(theme.PANEL)
        for sp in ax.spines.values():
            sp.set_edgecolor(theme.BORDER)
        ax.tick_params(colors=theme.FG_LBL)
        ax.text(0.5, 0.5, "Add elements to see Twiss functions",
                transform=ax.transAxes, color=theme.FG_LBL,
                ha="center", va="center", fontsize=theme.FONT_BODY)
        self._canvas.draw()

    def _redraw(self):
        r = self._result
        if r is None or r.n_elements == 0:
            self._draw_empty()
            return

        tp    = r.twiss_points
        s     = r.s_positions
        elems = getattr(r, '_elements', None)

        show_dx = self._cb_dx.isChecked() or self._cb_dy.isChecked()
        show_beta = (self._cb_bx.isChecked() or self._cb_by.isChecked() or
                     self._cb_ax.isChecked() or self._cb_ay.isChecked())

        self._fig.clear()

        # Layout: element bar on top, beta middle, dispersion bottom
        has_elem  = self._cb_elem.isChecked() and elems
        n_panels  = int(show_beta) + int(show_dx)
        if n_panels == 0:
            n_panels = 1

        heights = []
        if has_elem:   heights.append(0.06)
        if show_beta:  heights.append(0.47 if show_dx else 0.94)
        if show_dx:    heights.append(0.47 if show_beta else 0.94)

        # normalise
        total = sum(heights)
        heights = [h / total for h in heights]

        axes = []
        bottom = 0.0
        left, right, top_margin = 0.10, 0.97, 0.97
        for h in reversed(heights):
            ax = self._fig.add_axes(
                [left, bottom, right - left, h * (top_margin - 0.03)],
                frameon=True)
            axes.append(ax)
            bottom += h * (top_margin - 0.03) + 0.02

        axes = list(reversed(axes))   # top → bottom order

        ax_idx = 0

        # ── Element bar ──────────────────────────────────────────
        if has_elem:
            ax_e = axes[ax_idx]; ax_idx += 1
            ax_e.set_facecolor(theme.CRUST)
            ax_e.set_xlim(s[0], s[-1])
            ax_e.set_ylim(0, 1)
            ax_e.axis("off")

            self._elem_rects = []
            for i, elem in enumerate(elems):
                s0 = s[i]; s1 = s[i + 1]
                if s1 <= s0:
                    continue
                rect = Rectangle((s0, 0.05), s1 - s0, 0.9,
                                  facecolor=elem.color, edgecolor=theme.BORDER,
                                  linewidth=0.5, picker=True)
                ax_e.add_patch(rect)
                self._elem_rects.append((rect, i))

                # Label if wide enough
                width_frac = (s1 - s0) / (s[-1] - s[0])
                if width_frac > 0.04:
                    ax_e.text((s0 + s1) / 2, 0.5, elem.abbrev,
                              ha="center", va="center",
                              fontsize=max(5, theme.FONT_TINY - 1),
                              color=theme.CRUST, fontweight="bold",
                              clip_on=True)

        # ── Beta / alpha panel ────────────────────────────────────
        if show_beta:
            ax_b = axes[ax_idx]; ax_idx += 1
            ax_b.set_facecolor(theme.PANEL)
            for sp in ax_b.spines.values():
                sp.set_edgecolor(theme.BORDER)
            ax_b.tick_params(colors=theme.FG_LBL,
                             labelsize=theme.FONT_TINY)
            ax_b.set_ylabel("β (m) / α", color=theme.FG_LBL,
                            fontsize=theme.FONT_SMALL)
            ax_b.grid(True, color=theme.BORDER, alpha=0.25, ls="--")
            ax_b.axhline(0, color=theme.BORDER, lw=0.5)
            ax_b.set_xlim(s[0], s[-1])

            # Element boundary lines
            for si in s[1:-1]:
                ax_b.axvline(si, color=theme.BORDER,
                             lw=0.4, alpha=0.5, zorder=1)

            bx = [tp_i.betax  for tp_i in tp]
            by = [tp_i.betay  for tp_i in tp]
            ax = [tp_i.alphax for tp_i in tp]
            ay = [tp_i.alphay for tp_i in tp]

            if self._cb_bx.isChecked():
                ax_b.plot(s, bx, color=theme.TWISS_A, lw=2.0,
                          label="βx", zorder=3)
            if self._cb_by.isChecked():
                ax_b.plot(s, by, color=theme.TWISS_B, lw=2.0,
                          label="βy", zorder=3)
            if self._cb_ax.isChecked():
                ax_b.plot(s, ax, color=theme.TWISS_A, lw=1.5,
                          ls="--", label="αx", zorder=2)
            if self._cb_ay.isChecked():
                ax_b.plot(s, ay, color=theme.TWISS_B, lw=1.5,
                          ls="--", label="αy", zorder=2)

            ax_b.legend(fontsize=theme.FONT_TINY, framealpha=0.3,
                        facecolor=theme.PANEL, edgecolor=theme.BORDER,
                        labelcolor=theme.FG, loc="upper right")

            if not show_dx:
                ax_b.set_xlabel("s  (m)", color=theme.FG_LBL,
                                fontsize=theme.FONT_SMALL)

        # ── Dispersion panel ─────────────────────────────────────
        if show_dx:
            ax_d = axes[ax_idx]; ax_idx += 1
            ax_d.set_facecolor(theme.PANEL)
            for sp in ax_d.spines.values():
                sp.set_edgecolor(theme.BORDER)
            ax_d.tick_params(colors=theme.FG_LBL,
                             labelsize=theme.FONT_TINY)
            ax_d.set_ylabel("D (m)", color=theme.FG_LBL,
                            fontsize=theme.FONT_SMALL)
            ax_d.set_xlabel("s  (m)", color=theme.FG_LBL,
                            fontsize=theme.FONT_SMALL)
            ax_d.grid(True, color=theme.BORDER, alpha=0.25, ls="--")
            ax_d.axhline(0, color=theme.BORDER, lw=0.5)
            ax_d.set_xlim(s[0], s[-1])

            for si in s[1:-1]:
                ax_d.axvline(si, color=theme.BORDER,
                             lw=0.4, alpha=0.5, zorder=1)

            dx = [tp_i.Dx for tp_i in tp]
            dy = [tp_i.Dy for tp_i in tp]

            if self._cb_dx.isChecked():
                ax_d.plot(s, dx, color=theme.TWISS_A, lw=2.0,
                          label="Dx", zorder=3)
                ax_d.fill_between(s, dx, 0, alpha=0.12,
                                  color=theme.TWISS_A)
            if self._cb_dy.isChecked():
                ax_d.plot(s, dy, color=theme.TWISS_B, lw=2.0,
                          label="Dy", zorder=3)
                ax_d.fill_between(s, dy, 0, alpha=0.10,
                                  color=theme.TWISS_B)
            # Off-momentum overlay
            if abs(self._delta_p) > 1e-6 and self._cb_dx.isChecked():
                x_off = [self._delta_p * d for d in dx]
                ax_d.plot(s, x_off, color=theme.COLOR_PARTICLE,
                          lw=1.5, ls="--",
                          label=f"x_off (δ={self._delta_p*100:+.2f}%)",
                          zorder=4)

            ax_d.legend(fontsize=theme.FONT_TINY, framealpha=0.3,
                        facecolor=theme.PANEL, edgecolor=theme.BORDER,
                        labelcolor=theme.FG, loc="upper right")

        self._canvas.draw()

    # ── Click handler ─────────────────────────────────────────────

    _highlighted_idx: int | None = None

    def _on_click(self, event):
        """Click on element bar → emit element_selected."""
        if event.inaxes is None or self._result is None:
            return
        elems = getattr(self._result, '_elements', None)
        s_pos = self._result.s_positions
        if not elems:
            return
        sx = event.xdata
        if sx is None:
            return
        for i, elem in enumerate(elems):
            if s_pos[i] <= sx <= s_pos[i + 1]:
                uids = getattr(self._result, '_elem_uids', [])
                if i < len(uids):
                    self.element_selected.emit(uids[i])
                break
