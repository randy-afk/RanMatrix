"""
gui/phase_space.py
------------------
Interactive phase space panel — both (x,x') and (y,y') planes, tabbed.

Interactivity:
  - Click any ghost ellipse → highlights it, shows element label + s-position,
    emits element_selected(uid) so the lattice line highlights that block
  - highlight_element(uid) called from main_window when a block is clicked
    → highlights the corresponding ellipse in the plot
"""

from __future__ import annotations
import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QDoubleSpinBox, QTabWidget
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import matplotlib.patches as mpatches

import theme
from models.lattice import LatticeResult
from physics.matrices import (
    ellipse_points, propagate_particle, cumulative_products, propagate_twiss
)


# Colours for highlighted ellipse
_COL_HIGHLIGHT = "#FFD700"   # gold


class PhasePlaneCanvas(QWidget):
    """
    One phase-space plane (x or y).
    Emits element_selected(uid) when a ghost ellipse is clicked.
    """

    element_selected = Signal(str)   # uid of selected element

    def __init__(self, plane: str, parent=None):
        super().__init__(parent)
        assert plane in ("x", "y")
        self._plane  = plane
        self._result: LatticeResult | None = None
        self._emittance = 1e-6
        self._betax0 = 1.0;  self._alphax0 = 0.0
        self._betay0 = 1.0;  self._alphay0 = 0.0
        self._x0  = 1e-3;  self._xp0 = 0.0
        self._y0  = 0.0;   self._yp0 = 0.0
        self._show_ghosts   = True
        self._show_particle = True

        # Interactivity state
        # _ghost_lines[i] corresponds to cum[i+1]  (intermediate boundaries)
        # so element index = i  (0-based, matches R_each[i])
        self._ghost_lines: list[Line2D] = []
        self._ghost_elem_idx: list[int] = []   # element index for each ghost
        self._selected_elem_idx: int | None = None
        self._annot = None   # matplotlib annotation

        lay = QVBoxLayout(self)
        lay.setContentsMargins(2, 2, 2, 2)
        lay.setSpacing(3)

        # Controls
        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)

        self._cb_ghosts = QCheckBox("Ghosts")
        self._cb_ghosts.setChecked(True)
        self._cb_ghosts.setStyleSheet(
            f"color:{theme.FG_DIM}; font-size:{theme.FONT_TINY}px;")
        self._cb_ghosts.toggled.connect(self._on_toggle)

        self._cb_particle = QCheckBox("Particle")
        self._cb_particle.setChecked(True)
        self._cb_particle.setStyleSheet(
            f"color:{theme.FG_DIM}; font-size:{theme.FONT_TINY}px;")
        self._cb_particle.toggled.connect(self._on_toggle)

        em_lbl = QLabel("ε (mm·mrad):")
        em_lbl.setStyleSheet(
            f"color:{theme.FG_LBL}; font-size:{theme.FONT_TINY}px;")
        self._em_spin = QDoubleSpinBox()
        self._em_spin.setRange(1e-4, 100.0)
        self._em_spin.setValue(1.0)
        self._em_spin.setDecimals(3)
        self._em_spin.setFixedWidth(75)
        self._em_spin.setStyleSheet(
            f"background:{theme.MANTLE}; color:{theme.FG}; "
            f"border:1px solid {theme.BORDER}; border-radius:3px; "
            f"font-size:{theme.FONT_TINY}px;")
        self._em_spin.valueChanged.connect(lambda v: self._set_emit(v))

        u0_lbl = QLabel(f"{'x' if plane=='x' else 'y'}₀ (mm):")
        u0_lbl.setStyleSheet(
            f"color:{theme.FG_LBL}; font-size:{theme.FONT_TINY}px;")
        self._u0_spin = QDoubleSpinBox()
        self._u0_spin.setRange(-100, 100)
        self._u0_spin.setValue(1.0 if plane == 'x' else 0.0)
        self._u0_spin.setDecimals(3)
        self._u0_spin.setFixedWidth(70)
        self._u0_spin.setStyleSheet(
            f"background:{theme.MANTLE}; color:{theme.FG}; "
            f"border:1px solid {theme.BORDER}; border-radius:3px; "
            f"font-size:{theme.FONT_TINY}px;")
        self._u0_spin.valueChanged.connect(lambda v: self._set_u0(v))

        up0_lbl = QLabel(f"{'x' if plane=='x' else 'y'}'₀ (mrad):")
        up0_lbl.setStyleSheet(
            f"color:{theme.FG_LBL}; font-size:{theme.FONT_TINY}px;")
        self._up0_spin = QDoubleSpinBox()
        self._up0_spin.setRange(-100, 100)
        self._up0_spin.setValue(0.0)
        self._up0_spin.setDecimals(3)
        self._up0_spin.setFixedWidth(70)
        self._up0_spin.setStyleSheet(
            f"background:{theme.MANTLE}; color:{theme.FG}; "
            f"border:1px solid {theme.BORDER}; border-radius:3px; "
            f"font-size:{theme.FONT_TINY}px;")
        self._up0_spin.valueChanged.connect(lambda v: self._set_up0(v))

        for w in [self._cb_ghosts, self._cb_particle,
                  em_lbl, self._em_spin,
                  u0_lbl, self._u0_spin,
                  up0_lbl, self._up0_spin]:
            ctrl.addWidget(w)
        ctrl.addStretch()
        lay.addLayout(ctrl)

        # Info label — shows selected element name
        self._info_lbl = QLabel("")
        self._info_lbl.setStyleSheet(
            f"color:{_COL_HIGHLIGHT}; font-size:{theme.FONT_TINY}px; "
            f"background:transparent; font-weight:bold;")
        lay.addWidget(self._info_lbl)

        # Canvas
        self._fig = Figure(figsize=(5, 3.5), facecolor=theme.BG)
        self._canvas = FigureCanvasQTAgg(self._fig)
        self._ax = self._fig.add_subplot(111)
        self._fig.subplots_adjust(left=0.13, right=0.97, top=0.93, bottom=0.13)
        lay.addWidget(self._canvas, 1)

        # Connect mouse click
        self._fig.canvas.mpl_connect("button_press_event", self._on_click)

        self._draw_empty()

    # ── Slots ─────────────────────────────────────────────────────

    def _on_toggle(self):
        self._show_ghosts   = self._cb_ghosts.isChecked()
        self._show_particle = self._cb_particle.isChecked()
        self._redraw()

    def _set_emit(self, v):
        self._emittance = v * 1e-6
        self._redraw()

    def _set_u0(self, v):
        if self._plane == "x":
            self._x0 = v * 1e-3
        else:
            self._y0 = v * 1e-3
        self._redraw()

    def _set_up0(self, v):
        if self._plane == "x":
            self._xp0 = v * 1e-3
        else:
            self._yp0 = v * 1e-3
        self._redraw()

    # ── Public API ────────────────────────────────────────────────

    def update_result(self, result: LatticeResult):
        self._result = result
        self._selected_elem_idx = None
        self._info_lbl.setText("")
        tp0 = result.twiss_points[0]
        self._betax0  = tp0.betax;   self._alphax0 = tp0.alphax
        self._betay0  = tp0.betay;   self._alphay0 = tp0.alphay
        self._redraw()

    def highlight_element(self, uid: str | None):
        """Called from outside (e.g. lattice line click) — highlight that ellipse."""
        if self._result is None:
            return
        if uid is None:
            self._selected_elem_idx = None
            self._info_lbl.setText("")
            self._apply_highlight()
            return
        # Find index of uid in element list
        idx = next((i for i, e in enumerate(self._result.R_each)
                    if i < len(self._result.R_each)), None)
        # Match uid to element index via the lattice (stored on result via _elem_uids)
        if hasattr(self._result, '_elem_uids'):
            try:
                idx = self._result._elem_uids.index(uid)
            except ValueError:
                idx = None
        self._selected_elem_idx = idx
        self._apply_highlight()

    def highlight_by_index(self, idx: int | None):
        """Highlight ellipse by element index directly."""
        self._selected_elem_idx = idx
        self._apply_highlight()
        if idx is not None and self._result:
            self._update_info_label(idx)

    # ── Mouse interaction ─────────────────────────────────────────

    def _on_click(self, event):
        """Find the closest ghost ellipse to the click and select it."""
        if event.inaxes != self._ax:
            return
        if not self._ghost_lines:
            return

        cx, cy = event.xdata, event.ydata
        if cx is None or cy is None:
            return

        # Get axis scale to normalise distance
        xlim = self._ax.get_xlim()
        ylim = self._ax.get_ylim()
        xscale = xlim[1] - xlim[0]
        yscale = ylim[1] - ylim[0]
        if xscale < 1e-12 or yscale < 1e-12:
            return

        best_idx  = None
        best_dist = float("inf")

        for i, line in enumerate(self._ghost_lines):
            xd = line.get_xdata()
            yd = line.get_ydata()
            if len(xd) == 0:
                continue
            # Minimum distance from click to any point on this ellipse
            dx = (np.asarray(xd) - cx) / xscale
            dy = (np.asarray(yd) - cy) / yscale
            dist = float(np.min(np.sqrt(dx**2 + dy**2)))
            if dist < best_dist:
                best_dist = dist
                best_idx  = i

        # Accept if within ~5% of axis range
        if best_idx is not None and best_dist < 0.08:
            elem_idx = self._ghost_elem_idx[best_idx]
            self._selected_elem_idx = elem_idx
            self._apply_highlight()
            self._update_info_label(elem_idx)
            # Signal to main window
            if self._result and hasattr(self._result, '_elem_uids'):
                if elem_idx < len(self._result._elem_uids):
                    self.element_selected.emit(self._result._elem_uids[elem_idx])

    def _apply_highlight(self):
        """Update visual state of ghost lines without full redraw."""
        for i, line in enumerate(self._ghost_lines):
            elem_idx = self._ghost_elem_idx[i]
            if elem_idx == self._selected_elem_idx:
                line.set_color(_COL_HIGHLIGHT)
                line.set_linewidth(2.5)
                line.set_alpha(1.0)
                line.set_linestyle("-")
                line.set_zorder(5)
            else:
                line.set_color(theme.COLOR_GHOST)
                line.set_linewidth(0.6)
                line.set_alpha(0.25)
                line.set_linestyle("--")
                line.set_zorder(1)
        self._canvas.draw_idle()

    def _update_info_label(self, elem_idx: int):
        if self._result is None:
            return
        elems  = getattr(self._result, '_elements', None)
        s_pos  = self._result.s_positions
        if elems and elem_idx < len(elems):
            name = elems[elem_idx].label
            etype = elems[elem_idx].etype.value
            s    = s_pos[elem_idx + 1] if elem_idx + 1 < len(s_pos) else 0.0
            tp   = self._result.twiss_points[elem_idx + 1]
            b    = tp.betax if self._plane == "x" else tp.betay
            a    = tp.alphax if self._plane == "x" else tp.alphay
            self._info_lbl.setText(
                f"[{elem_idx+1}] {name}  ({etype})  "
                f"s={s:.3f}m   β={b:.4f}m   α={a:.4f}")
        else:
            s = s_pos[elem_idx + 1] if elem_idx + 1 < len(s_pos) else 0.0
            self._info_lbl.setText(f"Element [{elem_idx+1}]  s={s:.3f}m")

    # ── Drawing ───────────────────────────────────────────────────

    def _draw_empty(self):
        ax = self._ax
        ax.set_facecolor(theme.PANEL)
        p = self._plane
        ax.set_xlabel(f"{p}  (mm)", color=theme.FG_LBL)
        ax.set_ylabel(f"{p}'  (mrad)", color=theme.FG_LBL)
        ax.set_title(f"Phase Space  ({p}, {p}')",
                     color=theme.FG, fontsize=theme.FONT_SMALL)
        ax.tick_params(colors=theme.FG_LBL)
        for sp in ax.spines.values():
            sp.set_edgecolor(theme.BORDER)
        ax.text(0.5, 0.5, "Add elements to the lattice",
                transform=ax.transAxes, color=theme.FG_LBL,
                ha="center", va="center", fontsize=theme.FONT_BODY)
        self._canvas.draw()

    def _redraw(self):
        if self._result is None or self._result.n_elements == 0:
            self._ax.cla()
            self._draw_empty()
            return

        p     = self._plane
        ax    = self._ax
        ax.cla()
        color = theme.TWISS_A if p == "x" else theme.TWISS_B

        ax.set_facecolor(theme.PANEL)
        ax.set_xlabel(f"{p}  (mm)",
                      color=theme.FG_LBL, fontsize=theme.FONT_SMALL)
        ax.set_ylabel(f"{p}'  (mrad)",
                      color=theme.FG_LBL, fontsize=theme.FONT_SMALL)
        ax.set_title(f"Phase Space  ({p}, {p}')",
                     color=theme.FG, fontsize=theme.FONT_SMALL)
        ax.tick_params(colors=theme.FG_LBL, labelsize=theme.FONT_TINY)
        for sp in ax.spines.values():
            sp.set_edgecolor(theme.BORDER)
        ax.axhline(0, color=theme.BORDER, lw=0.5, ls="--")
        ax.axvline(0, color=theme.BORDER, lw=0.5, ls="--")

        R_each = self._result.R_each
        twiss  = self._result.twiss_points
        elems  = getattr(self._result, '_elements', None)
        s_pos  = self._result.s_positions

        beta0  = self._betax0  if p == "x" else self._betay0
        alpha0 = self._alphax0 if p == "x" else self._alphay0

        # Ghost ellipses — one per intermediate boundary
        # cum[k+1] = after element k  →  ghost index i maps to element index i
        self._ghost_lines     = []
        self._ghost_elem_idx  = []

        if self._show_ghosts:
            cum = cumulative_products(R_each)
            # boundaries 1 .. N-1  (skip entrance=0 and exit=N)
            for boundary_idx in range(1, len(cum) - 1):
                elem_idx = boundary_idx - 1   # element that just ended
                M_cum = cum[boundary_idx]
                tw = propagate_twiss(self._betax0, self._alphax0,
                                     self._betay0, self._alphay0, M_cum)
                b = tw["betax"] if p == "x" else tw["betay"]
                a = tw["alphax"] if p == "x" else tw["alphay"]
                if b <= 0:
                    continue

                gu, gup = ellipse_points(self._emittance, b, a)

                is_selected = (elem_idx == self._selected_elem_idx)
                lw    = 2.5  if is_selected else 0.6
                alpha = 1.0  if is_selected else 0.25
                ls    = "-"  if is_selected else "--"
                col   = _COL_HIGHLIGHT if is_selected else theme.COLOR_GHOST
                zo    = 5    if is_selected else 1

                # Get element name for label
                name = (elems[elem_idx].label
                        if elems and elem_idx < len(elems)
                        else f"E{elem_idx+1}")
                s_val = s_pos[boundary_idx] if boundary_idx < len(s_pos) else 0.0
                lbl   = f"{name}  s={s_val:.2f}m" if is_selected else None

                line, = ax.plot(gu*1e3, gup*1e3,
                                color=col, lw=lw, alpha=alpha,
                                ls=ls, zorder=zo,
                                label=lbl,
                                picker=True, pickradius=6)
                self._ghost_lines.append(line)
                self._ghost_elem_idx.append(elem_idx)

        # Exit ellipse
        tp_exit = twiss[-1]
        b_exit  = tp_exit.betax  if p == "x" else tp_exit.betay
        a_exit  = tp_exit.alphax if p == "x" else tp_exit.alphay
        if b_exit > 0:
            eu, eup = ellipse_points(self._emittance, b_exit, a_exit)
            ax.plot(eu*1e3, eup*1e3,
                    color=color, lw=2.0, zorder=3, label="Exit ellipse")

        # Entrance ellipse — orange dashed, always on top
        ei, eip = ellipse_points(self._emittance, beta0, alpha0)
        ax.plot(ei*1e3, eip*1e3,
                color=theme.ACCENT, lw=1.8, ls="--",
                alpha=0.9, zorder=4, label="Entrance ellipse")

        # Single particle
        if self._show_particle:
            traj = propagate_particle(self._x0, self._xp0,
                                      self._y0, self._yp0, R_each)
            if p == "x":
                us  = [v*1e3 for v in traj["x"]]
                ups = [v*1e3 for v in traj["xp"]]
                u0  = self._x0 * 1e3
            else:
                us  = [v*1e3 for v in traj["y"]]
                ups = [v*1e3 for v in traj["yp"]]
                u0  = self._y0 * 1e3

            ax.plot(us, ups, "o-", color=theme.COLOR_PARTICLE,
                    ms=4, lw=1.2, alpha=0.85, zorder=6,
                    label=f"Particle ({p}₀={u0:.2f}mm)")
            ax.plot(us[0],  ups[0],  "^",
                    color=theme.COLOR_PARTICLE, ms=8, zorder=7)
            ax.plot(us[-1], ups[-1], "v",
                    color=theme.COLOR_PARTICLE, ms=8, zorder=7)

        ax.legend(fontsize=theme.FONT_TINY, framealpha=0.3,
                  facecolor=theme.PANEL, edgecolor=theme.BORDER,
                  labelcolor=theme.FG)
        ax.grid(True, color=theme.BORDER, alpha=0.3, ls="--")
        self._canvas.draw()


class PhaseSpacePanel(QWidget):
    """Tabbed container for X and Y phase space planes."""

    element_selected = Signal(str)   # forwarded from either plane

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                background:{theme.PANEL}; border:1px solid {theme.BORDER};
                border-radius:4px;
            }}
            QTabBar::tab {{
                background:{theme.MANTLE}; color:{theme.FG_DIM};
                border:1px solid {theme.BORDER}; border-bottom:none;
                padding:3px 14px; font-size:{theme.FONT_TINY}px;
                border-top-left-radius:4px; border-top-right-radius:4px;
            }}
            QTabBar::tab:selected {{
                background:{theme.ACCENT}; color:{theme.CRUST};
                font-weight:bold;
            }}
            QTabBar::tab:hover:!selected {{
                background:{theme.SURFACE2}; color:{theme.FG};
            }}
        """)

        self._x_plane = PhasePlaneCanvas("x")
        self._y_plane = PhasePlaneCanvas("y")
        tabs.addTab(self._x_plane, "Phase Space  (x, x')")
        tabs.addTab(self._y_plane, "Phase Space  (y, y')")
        lay.addWidget(tabs)

        # Forward element_selected from both planes
        self._x_plane.element_selected.connect(self.element_selected)
        self._y_plane.element_selected.connect(self.element_selected)

    def update_result(self, result: LatticeResult):
        self._x_plane.update_result(result)
        self._y_plane.update_result(result)

    def highlight_element(self, uid: str | None, idx: int | None):
        """Highlight the ellipse for a given element index in both planes."""
        self._x_plane.highlight_by_index(idx)
        self._y_plane.highlight_by_index(idx)
