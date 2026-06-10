"""
gui/dispersion_panel.py — Dx, Dy, Dx', Dy' both planes + R56 + Δp/p slider.
"""
from __future__ import annotations
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QCheckBox, QTabWidget
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import theme
from models.lattice import LatticeResult


class DispersionPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._result: LatticeResult | None = None
        self._delta_p = 0.0
        theme.apply_mpl_theme()

        lay = QVBoxLayout(self); lay.setContentsMargins(4,4,4,4); lay.setSpacing(4)

        # Controls
        ctrl = QHBoxLayout()
        dp_lbl = QLabel("Δp/p:")
        dp_lbl.setStyleSheet(f"color:{theme.FG_LBL}; font-size:{theme.FONT_SMALL}px;")
        self._dp_slider = QSlider(Qt.Horizontal)
        self._dp_slider.setRange(-100, 100); self._dp_slider.setValue(0)
        self._dp_slider.setFixedWidth(150)
        self._dp_val = QLabel("0.00%")
        self._dp_val.setStyleSheet(f"color:{theme.FG}; font-size:{theme.FONT_SMALL}px; min-width:55px;")
        self._dp_slider.valueChanged.connect(self._on_dp)

        self._cb_dy = QCheckBox("Show Dy")
        self._cb_dy.setChecked(True)
        self._cb_dy.setStyleSheet(f"color:{theme.FG_DIM}; font-size:{theme.FONT_TINY}px;")
        self._cb_dy.toggled.connect(self._redraw)

        self._cb_primes = QCheckBox("Show D'")
        self._cb_primes.setChecked(False)
        self._cb_primes.setStyleSheet(f"color:{theme.FG_DIM}; font-size:{theme.FONT_TINY}px;")
        self._cb_primes.toggled.connect(self._redraw)

        for w in [dp_lbl, self._dp_slider, self._dp_val, self._cb_dy, self._cb_primes]:
            ctrl.addWidget(w)
        ctrl.addStretch()
        lay.addLayout(ctrl)

        # Canvas
        self._fig = Figure(figsize=(5, 3.2), facecolor=theme.BG)
        self._canvas = FigureCanvasQTAgg(self._fig)
        self._ax = self._fig.add_subplot(111)
        self._fig.subplots_adjust(left=0.12, right=0.97, top=0.93, bottom=0.12)
        lay.addWidget(self._canvas, 1)
        self._draw_empty()

    def _on_dp(self, v):
        self._delta_p = v / 1000.0
        self._dp_val.setText(f"{self._delta_p*100:+.2f}%")
        self._redraw()

    def update_result(self, result):
        self._result = result; self._redraw()

    def _draw_empty(self):
        ax = self._ax
        ax.set_facecolor(theme.PANEL)
        ax.set_xlabel("s  (m)", color=theme.FG_LBL)
        ax.set_ylabel("D  (m)", color=theme.FG_LBL)
        ax.set_title("Dispersion", color=theme.FG, fontsize=theme.FONT_SMALL)
        ax.tick_params(colors=theme.FG_LBL)
        for sp in ax.spines.values(): sp.set_edgecolor(theme.BORDER)
        ax.text(0.5, 0.5, "Add bending elements to generate dispersion",
                transform=ax.transAxes, color=theme.FG_LBL,
                ha="center", va="center", fontsize=theme.FONT_BODY)
        self._canvas.draw()

    def _redraw(self):
        if self._result is None or self._result.n_elements == 0:
            self._ax.cla(); self._draw_empty(); return

        ax = self._ax; ax.cla()
        ax.set_facecolor(theme.PANEL)
        ax.set_xlabel("s  (m)", color=theme.FG_LBL, fontsize=theme.FONT_SMALL)
        ax.set_ylabel("D  (m)", color=theme.FG_LBL, fontsize=theme.FONT_SMALL)
        ax.set_title("Dispersion — both planes", color=theme.FG, fontsize=theme.FONT_SMALL)
        ax.tick_params(colors=theme.FG_LBL, labelsize=theme.FONT_TINY)
        for sp in ax.spines.values(): sp.set_edgecolor(theme.BORDER)
        ax.axhline(0, color=theme.BORDER, lw=0.5, ls="--")

        s  = self._result.s_positions
        Dx = self._result.Dx_list
        Dy = self._result.Dy_list
        Dxp = self._result.Dxp_list
        Dyp = self._result.Dyp_list

        ax.plot(s, Dx, color=theme.TWISS_A, lw=2.0, label="Dx")
        ax.fill_between(s, Dx, 0, alpha=0.12, color=theme.TWISS_A)

        if self._cb_dy.isChecked():
            ax.plot(s, Dy, color=theme.TWISS_B, lw=2.0, label="Dy")
            ax.fill_between(s, Dy, 0, alpha=0.10, color=theme.TWISS_B)

        if self._cb_primes.isChecked():
            ax.plot(s, Dxp, color=theme.TWISS_A, lw=1.2, ls=":", label="Dx'")
            if self._cb_dy.isChecked():
                ax.plot(s, Dyp, color=theme.TWISS_B, lw=1.2, ls=":", label="Dy'")

        if abs(self._delta_p) > 1e-6:
            x_off = [self._delta_p * d for d in Dx]
            ax.plot(s, x_off, color=theme.COLOR_PARTICLE, lw=1.5, ls="--",
                    label=f"x_off (δ={self._delta_p*100:+.2f}%)")

        for s_i in self._result.s_positions[1:-1]:
            ax.axvline(s_i, color=theme.BORDER, lw=0.4, alpha=0.4)

        ax.legend(fontsize=theme.FONT_TINY, framealpha=0.3,
                  facecolor=theme.PANEL, edgecolor=theme.BORDER, labelcolor=theme.FG)
        ax.grid(True, color=theme.BORDER, alpha=0.25, ls="--")
        self._canvas.draw()
