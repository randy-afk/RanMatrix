"""
gui/main_window.py
------------------
Top-level application window.
Three-column splitter: Palette | Centre (lattice line + plots) | Right (matrix + Twiss)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QObject, QTimer
from PySide6.QtWidgets import (
    QMainWindow, QDialog, QToolButton, QWidget, QSplitter, QVBoxLayout, QHBoxLayout,
    QMenuBar, QMenu, QStatusBar, QLabel, QFileDialog, QMessageBox,
    QToolBar, QPushButton, QSizePolicy, QFrame
)
from PySide6.QtGui import QAction, QKeySequence, QFont, QPixmap

import theme
from models import Lattice, LatticeResult, LatticeHistory, Element, ElementType
from gui.palette_panel import PalettePanel
from gui.lattice_line import LatticeLine
from gui.matrix_panel import MatrixPanel
from gui.phase_space import PhaseSpacePanel
from gui.element_editor import ElementEditor
from gui.mode_bar import ModeBar
from gui.initial_conditions import InitialConditionsPanel
from gui.twiss_plot import TwissPlotPanel
from gui.step_mode import StepModePanel


PRESETS_PATH = Path(__file__).parent.parent / "presets" / "presets.json"


def _make_logo_pixmap(width: int = 220, height: int = 44) -> QPixmap:
    """
    Generate the RanMatrix logo inline as a QPixmap.
    No file I/O — rendered via matplotlib Agg into memory.
    """
    import io
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import theme as th

    dpi = 100
    fig = plt.figure(figsize=(width / dpi, height / dpi),
                     facecolor=th.CRUST)

    # Matrix mini-grid (left third)
    ax_m = fig.add_axes([0.01, 0.05, 0.22, 0.90])
    ax_m.set_facecolor(th.CRUST)
    ax_m.axis("off")
    n = 6; cell = 0.155
    M_vals = [[-0.45, 3.80, 0, 0, 0, 0.05],
              [-0.48, 1.82, 0, 0, 0, 0],
              [0, 0, 0.62, 2.14, 0, 0],
              [0, 0, -0.31, 0.62, 0, 0],
              [0, 0, 0, 0, 1.0, -3.0],
              [0, 0, 0, 0, 0, 1.0]]
    max_v = max(abs(M_vals[r][c]) for r in range(n) for c in range(n))
    for r in range(n):
        for c in range(n):
            v = M_vals[r][c]
            frac = abs(v) / max_v
            ri = int(0x23 + frac * (0xFD - 0x23))
            gi = int(0x44 + frac * (0xA7 - 0x44))
            bi = int(0x38 + frac * (0x69 - 0x38))
            ax_m.add_patch(plt.Rectangle(
                (c * cell, (n-1-r) * cell), cell*0.86, cell*0.86,
                facecolor=f"#{ri:02x}{gi:02x}{bi:02x}",
                edgecolor=th.BORDER, linewidth=0.2))
    ax_m.set_xlim(-0.02, n*cell+0.02); ax_m.set_ylim(-0.02, n*cell+0.02)

    # Phase space ellipse (middle)
    ax_e = fig.add_axes([0.24, 0.05, 0.20, 0.90])
    ax_e.set_facecolor(th.CRUST); ax_e.axis("off")
    phi = np.linspace(0, 2*np.pi, 200)
    for (b, a, col, lw, alpha) in [
        (5.0, 0.0, th.ACCENT,  1.4, 0.9),
        (2.5, -1.0, th.TWISS_A, 1.8, 1.0),
        (1.2, 0.5, th.BORDER,  0.6, 0.5),
    ]:
        g = (1+a**2)/b; eps=1.0
        x  =  np.sqrt(eps*b)*np.cos(phi)
        xp = -np.sqrt(eps/b)*(a*np.cos(phi)+np.sin(phi))
        ax_e.plot(x/max(abs(x))*0.45, xp/max(abs(xp))*0.45,
                  color=col, lw=lw, alpha=alpha)
    ax_e.axhline(0, color=th.BORDER, lw=0.4, alpha=0.4)
    ax_e.axvline(0, color=th.BORDER, lw=0.4, alpha=0.4)
    ax_e.set_xlim(-0.55, 0.55); ax_e.set_ylim(-0.55, 0.55)

    # Wordmark (right)
    ax_t = fig.add_axes([0.45, 0.0, 0.55, 1.0])
    ax_t.set_facecolor(th.CRUST); ax_t.axis("off")
    ax_t.text(0.04, 0.64, "RanMatrix",
              color=th.FG, fontsize=12, fontweight="bold",
              fontfamily="monospace", va="center", ha="left",
              transform=ax_t.transAxes)
    ax_t.text(0.04, 0.25, "v1.0.0  Beam Optics Explorer",
              color=th.FG_DIM, fontsize=6.5,
              va="center", ha="left", transform=ax_t.transAxes)
    from matplotlib.lines import Line2D
    ax_t.add_line(Line2D([0.04, 0.92], [0.46, 0.46],
                         transform=ax_t.transAxes,
                         color=th.ACCENT, lw=1.2))

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi,
                bbox_inches="tight", pad_inches=0.0,
                facecolor=th.CRUST)
    plt.close(fig)
    buf.seek(0)

    pix = QPixmap()
    pix.loadFromData(buf.read(), "PNG")
    return pix


class MainWindow(QMainWindow):

    # Emitted whenever the lattice changes — all panels connect to this
    lattice_changed = Signal(object)   # payload: LatticeResult

    def __init__(self):
        super().__init__()
        self.setWindowTitle("RanMatrix  v1.0.0")
        self.resize(1400, 860)
        self.setMinimumSize(900, 600)

        self._lattice  = Lattice()
        self._history  = LatticeHistory()
        self._result: LatticeResult | None = None
        self._busy = False          # debounce re-entry during batch edits

        # Push an initial empty state
        self._history.push(self._lattice.to_dict())

        self._build_menu()
        self._build_toolbar()
        self._build_central()
        self._build_statusbar()

        # Connect signals
        self._connect_signals()

        # Load FODO preset to start with something visible
        self._load_preset_by_name("FODO Cell")
        self._recompute()

    # ──────────────────────────────────────────────────────────────
    # Build UI
    # ──────────────────────────────────────────────────────────────

    def _build_menu(self):
        mb = self.menuBar()
        mb.setNativeMenuBar(False)

        # File
        file_menu = mb.addMenu("File")
        self._act_new      = QAction("New",        self, shortcut=QKeySequence.New)
        self._act_open     = QAction("Open…",      self, shortcut=QKeySequence.Open)
        self._act_save     = QAction("Save…",      self, shortcut=QKeySequence.Save)
        self._act_save_as  = QAction("Save As…",   self, shortcut=QKeySequence("Ctrl+Shift+S"))
        self._act_quit     = QAction("Quit",        self, shortcut=QKeySequence.Quit)
        for act in [self._act_new, self._act_open, self._act_save,
                    self._act_save_as, None, self._act_quit]:
            if act is None:
                file_menu.addSeparator()
            else:
                file_menu.addAction(act)

        # Edit
        edit_menu = mb.addMenu("Edit")
        self._act_undo = QAction("Undo", self, shortcut=QKeySequence.Undo)
        self._act_redo = QAction("Redo", self, shortcut=QKeySequence.Redo)
        self._act_clear = QAction("Clear Lattice", self)
        edit_menu.addAction(self._act_undo)
        edit_menu.addAction(self._act_redo)
        edit_menu.addSeparator()
        edit_menu.addAction(self._act_clear)

        # Presets
        presets_menu = mb.addMenu("Presets")
        self._load_preset_actions(presets_menu)

        # Export
        export_menu = mb.addMenu("Export")
        self._act_exp_elegant = QAction("Export → ELEGANT", self)
        self._act_exp_bmad    = QAction("Export → Bmad",    self)
        self._act_exp_numpy   = QAction("Export Matrix → numpy (.npy)", self)
        for act in [self._act_exp_elegant, self._act_exp_bmad,
                    None, self._act_exp_numpy]:
            if act is None:
                export_menu.addSeparator()
            else:
                export_menu.addAction(act)

        # Connect menu actions
        self._act_new.triggered.connect(self._on_new)
        self._act_open.triggered.connect(self._on_open)
        self._act_save.triggered.connect(self._on_save)
        self._act_save_as.triggered.connect(self._on_save_as)
        self._act_quit.triggered.connect(self.close)
        self._act_undo.triggered.connect(self._on_undo)
        self._act_redo.triggered.connect(self._on_redo)
        self._act_clear.triggered.connect(self._on_clear)
        self._act_exp_elegant.triggered.connect(self._on_export_elegant)
        self._act_exp_bmad.triggered.connect(self._on_export_bmad)
        self._act_exp_numpy.triggered.connect(self._on_export_numpy)

    def _load_preset_actions(self, menu: QMenu):
        try:
            data = json.loads(PRESETS_PATH.read_text())
            for preset in data["presets"]:
                act = QAction(preset["name"], self)
                act.triggered.connect(
                    lambda checked=False, p=preset: self._apply_preset(p)
                )
                menu.addAction(act)
        except Exception as e:
            menu.addAction(QAction(f"(presets unavailable: {e})", self))

    def _build_toolbar(self):
        tb = QToolBar("Main toolbar")
        tb.setMovable(False)
        tb.setStyleSheet(f"background:{theme.CRUST}; border-bottom: 1px solid {theme.BORDER};")
        self.addToolBar(Qt.TopToolBarArea, tb)

        # Logo
        logo_lbl = QLabel()
        pix = _make_logo_pixmap(220, 44)
        if not pix.isNull():
            logo_lbl.setPixmap(pix)
        else:
            logo_lbl.setText("RanMatrix")
            logo_lbl.setStyleSheet(
                f"color:{theme.FG}; font-weight:bold; "
                f"font-size:{theme.FONT_HEADER}px; padding:0 8px;")
        tb.addWidget(logo_lbl)

        sep_w2 = QWidget(); sep_w2.setFixedWidth(8)
        tb.addWidget(sep_w2)

        self._mode_bar = ModeBar(self._lattice)
        tb.addWidget(self._mode_bar)

        spacer = QWidget(); spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(spacer)

        # ── Toolbar button style helpers ──────────────────────────
        def _tb_btn(text: str, accent: bool = False,
                    tooltip: str = "") -> QToolButton:
            """Create a properly styled toolbar button."""
            b = QToolButton()
            b.setText(text)
            b.setToolButtonStyle(Qt.ToolButtonTextOnly)
            b.setFixedHeight(28)
            if tooltip:
                b.setToolTip(tooltip)
            if accent:
                b.setStyleSheet(f"""
                    QToolButton {{
                        background:{theme.ACCENT};
                        color:{theme.CRUST};
                        border:none;
                        border-radius:5px;
                        padding:0 12px;
                        font-size:{theme.FONT_SMALL}px;
                        font-weight:bold;
                    }}
                    QToolButton:hover {{
                        background:{theme.ACCENT2};
                    }}
                    QToolButton:pressed {{
                        background:{theme.ACCENT2};
                        padding-top:1px;
                    }}
                """)
            else:
                b.setStyleSheet(f"""
                    QToolButton {{
                        background:{theme.SURFACE2};
                        color:{theme.FG};
                        border:1px solid {theme.BORDER};
                        border-radius:5px;
                        padding:0 10px;
                        font-size:{theme.FONT_SMALL}px;
                    }}
                    QToolButton:hover {{
                        background:{theme.ACCENT};
                        color:{theme.CRUST};
                        border-color:{theme.ACCENT};
                    }}
                    QToolButton:pressed {{
                        background:{theme.ACCENT2};
                        color:{theme.CRUST};
                    }}
                    QToolButton:disabled {{
                        background:{theme.MANTLE};
                        color:{theme.FG_LBL};
                        border-color:{theme.MANTLE};
                    }}
                """)
            return b

        # Font scale
        from PySide6.QtWidgets import QSlider, QLabel as QL
        font_lbl = QL("  Text size:")
        font_lbl.setStyleSheet(
            f"color:{theme.FG_LBL}; font-size:{theme.FONT_SMALL}px; "
            f"background:transparent;")
        tb.addWidget(font_lbl)

        self._font_slider = QSlider(Qt.Horizontal)
        self._font_slider.setRange(7, 18)
        self._font_slider.setValue(10)
        self._font_slider.setFixedWidth(90)
        self._font_slider.setToolTip("Font scale")
        self._font_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background:{theme.MANTLE}; height:4px; border-radius:2px;}}
            QSlider::handle:horizontal {{
                background:{theme.ACCENT}; width:12px; height:12px;
                margin:-4px 0; border-radius:6px;}}
            QSlider::sub-page:horizontal {{
                background:{theme.ACCENT}; border-radius:2px;}}
        """)
        self._font_slider.valueChanged.connect(self._on_font_scale_changed)
        tb.addWidget(self._font_slider)

        # Spacer
        sp2 = QWidget(); sp2.setFixedWidth(10); tb.addWidget(sp2)

        # Beam Setup button (accent)
        self._btn_beam_setup = _tb_btn(
            "⚙  Beam Setup", accent=True,
            tooltip="Edit initial Twiss, dispersion, emittance and particle conditions")
        self._btn_beam_setup.clicked.connect(self._on_beam_setup)
        tb.addWidget(self._btn_beam_setup)

        sp3 = QWidget(); sp3.setFixedWidth(6); tb.addWidget(sp3)

        # Undo / Redo
        self._btn_undo = _tb_btn("↩  Undo", tooltip="Undo last change  (Ctrl+Z)")
        self._btn_redo = _tb_btn("↪  Redo", tooltip="Redo  (Ctrl+Y)")
        tb.addWidget(self._btn_undo)
        sp4 = QWidget(); sp4.setFixedWidth(3); tb.addWidget(sp4)
        tb.addWidget(self._btn_redo)

        self._btn_undo.clicked.connect(self._on_undo)
        self._btn_redo.clicked.connect(self._on_redo)

    def _build_central(self):
        # Root horizontal splitter: palette | centre | right
        root = QSplitter(Qt.Horizontal)
        root.setChildrenCollapsible(False)
        self.setCentralWidget(root)

        # Left: element palette
        self._palette = PalettePanel()
        root.addWidget(self._palette)

        # Centre: lattice line on top, tabbed plots below
        centre = QWidget()
        centre_layout = QVBoxLayout(centre)
        centre_layout.setContentsMargins(4, 4, 4, 4)
        centre_layout.setSpacing(4)

        self._lattice_line = LatticeLine()
        self._lattice_line.setFixedHeight(90)
        centre_layout.addWidget(self._lattice_line)

        # Centre bottom: vertical splitter — phase space | dispersion (tabbed)
        from PySide6.QtWidgets import QTabWidget
        self._centre_tabs = QTabWidget()
        self._phase_space  = PhaseSpacePanel()
        self._twiss_plot   = TwissPlotPanel()
        self._step_panel   = StepModePanel()
        self._centre_tabs.addTab(self._phase_space, "Phase Space")
        self._centre_tabs.addTab(self._twiss_plot,  "Twiss / Dispersion")
        self._centre_tabs.addTab(self._step_panel,  "Step Mode")
        centre_layout.addWidget(self._centre_tabs)

        root.addWidget(centre)

        # Right: matrix panel on top, Twiss below
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(4, 4, 4, 4)
        right_layout.setSpacing(4)

        self._matrix_panel = MatrixPanel()
        right_layout.addWidget(self._matrix_panel, 1)

        # IC panel lives in a dialog, created here, shown via toolbar button
        self._ic_panel = InitialConditionsPanel()
        self._ic_dialog = QDialog(self)
        self._ic_dialog.setWindowTitle("Beam Setup — Initial Conditions")
        self._ic_dialog.setMinimumWidth(480)
        ic_dlg_lay = QVBoxLayout(self._ic_dialog)
        ic_dlg_lay.setContentsMargins(0, 0, 0, 0)
        ic_dlg_lay.addWidget(self._ic_panel)

        root.addWidget(right)

        # Proportional widths: 1 : 3 : 2
        root.setSizes([220, 700, 420])

        # Element editor (slides in as a dock-like panel over centre — Phase 2: floating dialog for now)
        self._element_editor = ElementEditor(parent=self)
        self._element_editor.hide()

    def _build_statusbar(self):
        sb = self.statusBar()
        self._status_elements = QLabel("0 elements")
        self._status_length   = QLabel("L = 0.00 m")
        self._status_stable   = QLabel("")
        self._status_tune     = QLabel("")
        for lbl in [self._status_elements, self._status_length,
                    self._status_stable, self._status_tune]:
            lbl.setStyleSheet(f"color:{theme.FG_DIM}; padding: 0 8px;")
            sb.addWidget(lbl)

        # Author signature — permanent right-side widget
        self._status_author = QLabel(
            "RanMatrix v1.0.0  |  Randika Gamage  |  "
            "Support: Absolutely not. Figure it out.")
        self._status_author.setStyleSheet(
            f"color:{theme.FG_LBL}; font-size:{theme.FONT_TINY}px; "
            f"padding:0 10px;")
        sb.addPermanentWidget(self._status_author)

    # ──────────────────────────────────────────────────────────────
    # Signal wiring
    # ──────────────────────────────────────────────────────────────

    def _connect_signals(self):
        # Palette → append element
        self._palette.element_requested.connect(self._on_element_requested)

        # Lattice line → user interactions
        self._lattice_line.element_selected.connect(self._on_element_selected)
        self._lattice_line.element_double_clicked.connect(self._on_element_double_clicked)
        self._lattice_line.element_removed.connect(self._on_element_removed)
        self._lattice_line.order_changed.connect(self._on_order_changed)

        # Element editor → param changes
        self._element_editor.params_changed.connect(self._on_params_changed)
        self._element_editor.element_closed.connect(
            lambda: self._element_editor.hide()
        )

        # Mode bar → lattice mode / linear toggle
        self._mode_bar.mode_changed.connect(self._on_mode_changed)
        self._mode_bar.linear_changed.connect(self._on_linear_changed)

        # Lattice changed → all panels
        self.lattice_changed.connect(self._matrix_panel.update_result)
        self.lattice_changed.connect(self._phase_space.update_result)
        self.lattice_changed.connect(self._twiss_plot.update_result)
        self.lattice_changed.connect(self._step_panel.update_result)
        self.lattice_changed.connect(self._on_result_for_ic)

        # Initial conditions → update lattice and recompute
        self._ic_panel.conditions_changed.connect(self._on_conditions_changed)
        # Phase space ellipse click → highlight element block + matrix panel
        self._phase_space.element_selected.connect(self._on_ellipse_selected)
        # Twiss plot element bar click
        self._twiss_plot.element_selected.connect(self._on_ellipse_selected)
        # Step mode → highlight current element block
        self._step_panel.step_changed.connect(self._on_step_changed)

    # ──────────────────────────────────────────────────────────────
    # Core: recompute + broadcast
    # ──────────────────────────────────────────────────────────────

    def _recompute(self, push_history: bool = False):
        if self._busy:
            return
        self._result = self._lattice.compute()

        if push_history:
            self._history.push(self._lattice.to_dict())

        # Refresh lattice line display
        self._lattice_line.set_elements(self._lattice.elements)

        # Broadcast
        self.lattice_changed.emit(self._result)

        # Status bar
        self._update_statusbar(self._result)
        self._update_undo_buttons()

    def _update_statusbar(self, result: LatticeResult):
        n = result.n_elements
        L = result.s_positions[-1] if result.s_positions else 0.0
        self._status_elements.setText(f"{n} element{'s' if n != 1 else ''}")
        self._status_length.setText(f"L = {L:.3f} m")

        if result.stable:
            self._status_stable.setText("✓ STABLE")
            self._status_stable.setStyleSheet(
                f"color:{theme.SUCCESS}; padding:0 8px; font-weight:bold;")
        else:
            self._status_stable.setText("✗ UNSTABLE")
            self._status_stable.setStyleSheet(
                f"color:{theme.ERROR}; padding:0 8px; font-weight:bold;")

        if result.Qx is not None and result.Qy is not None:
            self._status_tune.setText(f"Qx = {result.Qx:.4f}   Qy = {result.Qy:.4f}")
            self._status_tune.setStyleSheet(f"color:{theme.ACCENT}; padding:0 8px;")
        elif result.Qx is not None:
            self._status_tune.setText(f"Qx = {result.Qx:.4f}")
            self._status_tune.setStyleSheet(f"color:{theme.ACCENT}; padding:0 8px;")
        else:
            self._status_tune.setText("")

    def _update_undo_buttons(self):
        self._btn_undo.setEnabled(self._history.can_undo())
        self._btn_redo.setEnabled(self._history.can_redo())
        self._act_undo.setEnabled(self._history.can_undo())
        self._act_redo.setEnabled(self._history.can_redo())

    # ──────────────────────────────────────────────────────────────
    # Slot handlers
    # ──────────────────────────────────────────────────────────────

    def _on_element_requested(self, etype: ElementType):
        """User clicked an element in the palette — append to lattice."""
        from models.element import make_element
        elem = make_element(etype)
        self._lattice.append(elem)
        self._recompute(push_history=True)

    def _on_element_selected(self, uid: str):
        """Single click — highlight only. No editor."""
        elem = self._lattice.get(uid)
        if elem:
            idx = next((i for i, e in enumerate(self._lattice.elements)
                        if e.uid == uid), None)
            self._matrix_panel.set_selected_element(uid, idx, elem.label)
            self._phase_space.highlight_element(uid, idx)
            self._twiss_plot.highlight_element(uid, idx)

    def _on_element_double_clicked(self, uid: str):
        """Double click — open element editor."""
        elem = self._lattice.get(uid)
        if elem:
            self._element_editor.set_element(elem)
            self._element_editor.show()
            self._element_editor.raise_()

    def _on_beam_setup(self):
        """Open the Beam Setup dialog."""
        self._ic_dialog.show()
        self._ic_dialog.raise_()
        self._ic_dialog.activateWindow()

    def _on_conditions_changed(self, cond: dict):
        """Initial conditions changed — apply to lattice and recompute."""
        for k, v in cond.items():
            if hasattr(self._lattice, k):
                setattr(self._lattice, k, v)
        self._recompute(push_history=True)

    def _on_result_for_ic(self, result):
        """Update IC panel with periodic solution in ring mode."""
        self._ic_panel.update_from_result(result, self._lattice)

    def _on_step_changed(self, elem_idx: int):
        """Step mode — highlight block only, no editor."""
        if not self._lattice.elements or elem_idx >= len(self._lattice.elements):
            return
        uid  = self._lattice.elements[elem_idx].uid
        name = self._lattice.elements[elem_idx].label
        self._lattice_line._on_block_selected(uid)
        self._matrix_panel.set_selected_element(uid, elem_idx, name)
        self._phase_space.highlight_by_index(elem_idx)

    def _on_ellipse_selected(self, uid: str):
        """Ellipse/Twiss plot click — highlight block + matrix. No editor."""
        elem = self._lattice.get(uid)
        if elem:
            idx = next((i for i, e in enumerate(self._lattice.elements)
                        if e.uid == uid), None)
            self._lattice_line._on_block_selected(uid)
            self._matrix_panel.set_selected_element(uid, idx, elem.label)

    def _on_element_removed(self, uid: str):
        self._lattice.remove(uid)
        self._element_editor.hide()
        self._matrix_panel.set_selected_element(None, None)
        self._recompute(push_history=True)

    def _on_order_changed(self, uids: list[str]):
        """Drag-reorder: rebuild element list from new uid order."""
        elem_map = {e.uid: e for e in self._lattice.elements}
        self._lattice.elements = [elem_map[uid] for uid in uids if uid in elem_map]
        self._recompute(push_history=True)

    def _on_params_changed(self, uid: str, params: dict):
        elem = self._lattice.get(uid)
        if elem:
            elem.params.update(params)
            self._recompute(push_history=True)

    def _on_mode_changed(self, mode: str):
        self._lattice.mode = mode
        self._ic_panel.set_mode(mode == "ring")
        self._recompute()

    def _on_linear_changed(self, linear: bool):
        self._lattice.linear = linear
        self._recompute()

    def _on_font_scale_changed(self, value: int):
        """Slider value 7–18 → scale 0.7–1.8. Rebuilds QSS and reapplies."""
        scale = value / 10.0
        theme.set_font_scale(scale)
        from PySide6.QtWidgets import QApplication
        QApplication.instance().setStyleSheet(theme.qss_base())
        theme.apply_mpl_theme()
        # Force all matplotlib canvases to redraw at new font size
        if self._result:
            self.lattice_changed.emit(self._result)

    # ── Undo / redo ─────────────────────────────────────────────

    def _on_undo(self):
        state = self._history.undo()
        if state:
            self._busy = True
            self._lattice = Lattice.from_dict(state)
            self._busy = False
            self._recompute()

    def _on_redo(self):
        state = self._history.redo()
        if state:
            self._busy = True
            self._lattice = Lattice.from_dict(state)
            self._busy = False
            self._recompute()

    # ── File ops ────────────────────────────────────────────────

    def _on_new(self):
        if QMessageBox.question(self, "New", "Clear the current lattice?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self._lattice = Lattice()
            self._history.clear()
            self._history.push(self._lattice.to_dict())
            self._recompute()

    def _on_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open session", "", "JSON files (*.json)")
        if path:
            try:
                self._lattice = Lattice.from_json(Path(path).read_text())
                self._history.clear()
                self._history.push(self._lattice.to_dict())
                self._recompute()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not load file:\n{e}")

    def _on_save(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save session", "lattice.json", "JSON files (*.json)")
        if path:
            Path(path).write_text(self._lattice.to_json())

    def _on_save_as(self):
        self._on_save()

    def _on_clear(self):
        self._lattice.clear()
        self._recompute(push_history=True)

    # ── Export ──────────────────────────────────────────────────

    def _on_export_elegant(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export ELEGANT", "lattice.lte", "ELEGANT (*.lte *.ele)")
        if path:
            Path(path).write_text(self._lattice.to_elegant())

    def _on_export_bmad(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Bmad", "lattice.bmad", "Bmad (*.bmad *.lat)")
        if path:
            Path(path).write_text(self._lattice.to_bmad())

    def _on_export_numpy(self):
        import numpy as np
        if self._result is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export matrix", "M_total.npy", "NumPy (*.npy)")
        if path:
            np.save(path, self._result.R)

    # ── Presets ─────────────────────────────────────────────────

    def _load_preset_by_name(self, name: str):
        try:
            data = json.loads(PRESETS_PATH.read_text())
            for preset in data["presets"]:
                if preset["name"] == name:
                    self._apply_preset(preset)
                    return
        except Exception:
            pass

    def _apply_preset(self, preset: dict):
        lat_dict = {
            "version": 1,
            "mode":       preset.get("mode", "linac"),
            "linear":     True,
            "betax0":     preset.get("beta0", 1.0),
            "alphax0":    preset.get("alpha0", 0.0),
            "betay0":     preset.get("beta0", 1.0),
            "alphay0":    0.0,
            "Dx0":        0.0,
            "Dpx0":       0.0,
            "emittance":  preset.get("emittance", 1e-6),
            "x0":         1e-3,
            "xp0":        0.0,
            "delta_p":    0.0,
            "elements":   preset["elements"],
        }
        self._lattice = Lattice.from_dict(lat_dict)
        self._history.clear()
        self._history.push(self._lattice.to_dict())
        self._mode_bar.set_state(self._lattice)
        self._ic_panel.set_from_lattice(self._lattice)
        self._ic_panel.set_mode(self._lattice.mode == "ring")
        self._recompute()
