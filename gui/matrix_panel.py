"""
gui/matrix_panel.py
-------------------
Right-column matrix display.
Uses QPainter-based custom widgets for matrix cells — completely bypasses
Qt stylesheet cascade issues.
"""

from __future__ import annotations
import numpy as np
from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
    QFrame, QTabWidget, QScrollArea, QComboBox, QCheckBox, QSizePolicy
)
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QFontMetrics
import theme
from models.lattice import LatticeResult
from physics.matrices import to_bmad, IMPORTANT_T_TERMS, COORD_LABELS


# ─────────────────────────────────────────────────────────────────────────────
# Color helpers
# ─────────────────────────────────────────────────────────────────────────────

def _cell_bg(value: float, max_abs: float) -> QColor:
    """Interpolate MANTLE → warm orange based on |value|/max_abs."""
    if max_abs < 1e-14:
        return QColor(theme.MANTLE)
    frac = min(abs(value) / max_abs, 1.0)
    r = int(0x1E + frac * (0xFD - 0x1E))
    g = int(0x3A + frac * (0xA7 - 0x3A))
    b = int(0x30 + frac * (0x69 - 0x30))
    return QColor(r, g, b)


# ─────────────────────────────────────────────────────────────────────────────
# MatrixCell — fully custom-painted widget, zero stylesheet involvement
# ─────────────────────────────────────────────────────────────────────────────

CELL_W = 64
CELL_H = 28

class MatrixCell(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(CELL_W, CELL_H)
        self._value: float | None = None
        self._max_abs: float = 1.0
        self._blank = True

    def set_val(self, value: float, max_abs: float):
        self._value   = value
        self._max_abs = max_abs
        self._blank   = False
        self.update()

    def clear(self):
        self._value = None
        self._blank = True
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)

        if self._blank or self._value is None:
            # Blank cell
            p.fillRect(self.rect(), QColor(theme.MANTLE))
            p.setPen(QColor(theme.BORDER))
            p.drawRect(self.rect().adjusted(0, 0, -1, -1))
            p.setPen(QColor(theme.FG_LBL))
            f = QFont("monospace", 8)
            p.setFont(f)
            p.drawText(self.rect(), Qt.AlignCenter, "—")
        else:
            v = self._value
            bg = _cell_bg(v, self._max_abs)
            p.fillRect(self.rect(), bg)
            p.setPen(QColor(theme.BORDER))
            p.drawRect(self.rect().adjusted(0, 0, -1, -1))

            # Text colour: bright if significant, dim if near zero
            if abs(v) > self._max_abs * 0.001:
                fg = QColor(theme.FG)
            else:
                fg = QColor(theme.FG_LBL)
            p.setPen(fg)

            f = QFont("monospace", 8)
            f.setBold(True)
            p.setFont(f)

            if abs(v) < 9999.5:
                txt = f"{v:+.3f}"
            else:
                txt = f"{v:+.1e}"
            p.drawText(self.rect(), Qt.AlignCenter, txt)

        p.end()


# ─────────────────────────────────────────────────────────────────────────────
# 6×6 matrix widget — grid of MatrixCell
# ─────────────────────────────────────────────────────────────────────────────

class Matrix6x6Widget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        grid = QGridLayout()
        grid.setSpacing(1)
        grid.setContentsMargins(0, 0, 0, 0)

        # Corner spacer
        corner = QWidget(); corner.setFixedSize(16, 16)
        grid.addWidget(corner, 0, 0)

        # Column headers
        self._col_hdrs: list[QLabel] = []
        for c in range(6):
            lbl = QLabel(str(c + 1))
            lbl.setFixedSize(CELL_W, 16)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFont(QFont("sans-serif", 8))
            lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
            self._col_hdrs.append(lbl)
            grid.addWidget(lbl, 0, c + 1)

        # Rows
        self._cells: list[list[MatrixCell]] = []
        for r in range(6):
            row_lbl = QLabel(str(r + 1))
            row_lbl.setFixedSize(16, CELL_H)
            row_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row_lbl.setFont(QFont("sans-serif", 8))
            grid.addWidget(row_lbl, r + 1, 0)

            row_cells = []
            for c in range(6):
                cell = MatrixCell()
                grid.addWidget(cell, r + 1, c + 1)
                row_cells.append(cell)
            self._cells.append(row_cells)

        outer.addLayout(grid)
        self._set_header_colors()

    def _set_header_colors(self):
        fg = theme.FG_LBL
        for lbl in self._col_hdrs:
            lbl.setStyleSheet(f"color:{fg}; background:transparent;")

    def set_coord_labels(self, names: list[str]):
        """Update column header text with coordinate names."""
        for i, lbl in enumerate(self._col_hdrs):
            lbl.setText(names[i] if i < len(names) else str(i+1))

    def set_matrix(self, M: np.ndarray):
        max_abs = float(np.abs(M).max())
        if max_abs < 1e-14:
            max_abs = 1.0
        for r in range(6):
            for c in range(6):
                self._cells[r][c].set_val(float(M[r, c]), max_abs)

    def clear(self):
        for row in self._cells:
            for cell in row:
                cell.clear()


# ─────────────────────────────────────────────────────────────────────────────
# StatBadge — also fully painted to avoid cascade
# ─────────────────────────────────────────────────────────────────────────────

class StatBadge(QWidget):
    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(60)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 3, 6, 3)
        lay.setSpacing(1)

        self._lbl_w = QLabel(label)
        self._lbl_w.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._val_w = QLabel("—")
        self._val_w.setAttribute(Qt.WA_TransparentForMouseEvents)

        self._lbl_color  = theme.FG_LBL
        self._val_color  = theme.FG
        self._lbl_fsize  = theme.FONT_TINY
        self._val_fsize  = theme.FONT_SMALL

        self._apply_styles()
        lay.addWidget(self._lbl_w)
        lay.addWidget(self._val_w)

    def _apply_styles(self):
        self.setStyleSheet(f"background:{theme.MANTLE}; border-radius:4px;")
        self._lbl_w.setStyleSheet(
            f"background:transparent; color:{self._lbl_color}; font-size:{self._lbl_fsize}px;")
        self._val_w.setStyleSheet(
            f"background:transparent; color:{self._val_color}; "
            f"font-size:{self._val_fsize}px; font-weight:bold; font-family:monospace;")

    def set(self, text: str, color: str = None):
        self._val_color = color or theme.FG
        self._val_w.setText(text)
        self._val_w.setStyleSheet(
            f"background:transparent; color:{self._val_color}; "
            f"font-size:{self._val_fsize}px; font-weight:bold; font-family:monospace;")


# ─────────────────────────────────────────────────────────────────────────────
# Section header helper
# ─────────────────────────────────────────────────────────────────────────────

def _hdr(text: str) -> QWidget:
    """Orange pill header — painted directly so it's immune to cascade."""
    w = QWidget()
    w.setFixedHeight(22)
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    inner = QLabel(text)
    inner.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
    inner.setFont(QFont("sans-serif", theme.FONT_SMALL, QFont.Bold))
    inner.setStyleSheet(
        f"background:{theme.ACCENT}; color:{theme.CRUST}; "
        f"padding:2px 10px; border-radius:4px; letter-spacing:1px;")
    lay.addWidget(inner)
    lay.addStretch()
    return w


def _sep() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    f.setFixedHeight(1)
    f.setStyleSheet(f"background:{theme.BORDER};")
    return f


# ─────────────────────────────────────────────────────────────────────────────
# T tensor panel
# ─────────────────────────────────────────────────────────────────────────────

class TTensorPanel(QWidget):
    """
    T tensor browser.
    Rebuilds by replacing the scroll widget entirely — avoids deleteLater
    timing issues with QGridLayout.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._T = np.zeros((6, 6, 6))

        lay = QVBoxLayout(self)
        lay.setContentsMargins(2, 2, 2, 2)
        lay.setSpacing(4)

        ctrl = QHBoxLayout()
        self._cb_all = QCheckBox("Show all non-zero")
        self._cb_all.setStyleSheet(
            f"color:{theme.FG_DIM}; font-size:{theme.FONT_TINY}px;")
        self._cb_all.toggled.connect(self._rebuild)
        ctrl.addWidget(self._cb_all)
        ctrl.addStretch()
        lay.addLayout(ctrl)

        # Scroll area — we replace its widget on every rebuild
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("QScrollArea { border:none; }")
        lay.addWidget(self._scroll, 1)

        self._rebuild()

    def set_T(self, T: np.ndarray):
        self._T = T
        self._rebuild()

    def _rebuild(self):
        show_all = self._cb_all.isChecked()
        max_abs  = float(np.abs(self._T).max())
        all_zero = max_abs < 1e-30

        # Build term list
        if show_all and not all_zero:
            terms = []
            for i in range(6):
                for j in range(6):
                    for k in range(j, 6):
                        v = float(self._T[i, j, k])
                        if abs(v) > max_abs * 1e-8:
                            terms.append((None, f"T{i+1}{j+1}{k+1}", "—", v))
        else:
            terms = [
                (cat, nm, desc, float(self._T[i, j, k]))
                for i, j, k, nm, cat, desc, *_ in IMPORTANT_T_TERMS
            ]

        # Build a fresh widget — no deleteLater timing issues
        container = QWidget()
        container.setStyleSheet(f"background:{theme.PANEL};")
        vlay = QVBoxLayout(container)
        vlay.setContentsMargins(4, 4, 4, 4)
        vlay.setSpacing(0)

        # Header row
        hrow = QHBoxLayout()
        hrow.setSpacing(4)
        for txt, w in [("Term", 60), ("Value", 100), ("Description", 220)]:
            lbl = QLabel(txt)
            lbl.setFixedWidth(w)
            lbl.setFont(QFont("sans-serif", theme.FONT_TINY, QFont.Bold))
            lbl.setStyleSheet(f"color:{theme.ACCENT}; background:transparent;")
            hrow.addWidget(lbl)
        hrow.addStretch()
        vlay.addLayout(hrow)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{theme.BORDER};")
        vlay.addWidget(sep)

        last_cat = None
        for entry in terms:
            cat, name, desc, v = entry

            # Category separator header (curated mode only)
            if not show_all and cat != last_cat:
                cat_row = QHBoxLayout()
                cat_lbl = QLabel(f"  {cat}")
                cat_lbl.setFont(QFont("sans-serif", theme.FONT_TINY, QFont.Bold))
                cat_lbl.setStyleSheet(
                    f"color:{theme.CRUST}; background:{theme.SURFACE2}; "
                    f"padding:1px 6px; border-radius:3px;")
                cat_row.addWidget(cat_lbl)
                cat_row.addStretch()
                vlay.addSpacing(3)
                vlay.addLayout(cat_row)
                last_cat = cat

            # Value colour based on magnitude
            if max_abs > 1e-30 and abs(v) > max_abs * 0.001:
                val_color = theme.FG
                name_color = theme.FG
            elif max_abs > 1e-30 and abs(v) > max_abs * 1e-8:
                val_color = theme.FG_DIM
                name_color = theme.FG_DIM
            else:
                val_color = theme.FG_LBL
                name_color = theme.FG_LBL

            row = QHBoxLayout()
            row.setSpacing(4)
            row.setContentsMargins(0, 1, 0, 1)

            nm_lbl = QLabel(name)
            nm_lbl.setFixedWidth(60)
            nm_lbl.setFont(QFont("monospace", theme.FONT_TINY, QFont.Bold))
            nm_lbl.setStyleSheet(f"color:{name_color}; background:transparent;")

            val_lbl = QLabel(f"{v:+.4e}")
            val_lbl.setFixedWidth(100)
            val_lbl.setFont(QFont("monospace", theme.FONT_TINY))
            val_lbl.setStyleSheet(f"color:{val_color}; background:transparent;")

            desc_lbl = QLabel(desc)
            desc_lbl.setFont(QFont("sans-serif", theme.FONT_TINY))
            desc_lbl.setStyleSheet(f"color:{theme.FG_LBL}; background:transparent;")

            row.addWidget(nm_lbl)
            row.addWidget(val_lbl)
            row.addWidget(desc_lbl)
            row.addStretch()
            vlay.addLayout(row)

        vlay.addStretch()

        # Swap in the new widget
        self._scroll.setWidget(container)


# ─────────────────────────────────────────────────────────────────────────────
# Main MatrixPanel
# ─────────────────────────────────────────────────────────────────────────────



# ─────────────────────────────────────────────────────────────────────────────
# Twiss transport 3×3 and dispersion vector helpers
# ─────────────────────────────────────────────────────────────────────────────

def _twiss3_from_R2(M2: np.ndarray) -> np.ndarray:
    """
    Build the 3×3 Courant-Snyder transport matrix from a 2×2 R block.
    Maps (β, α, γ) at entrance to (β, α, γ) at exit.

    T = [ M11²        -2·M11·M12     M12²     ]
        [ -M21·M11   M11·M22+M12·M21  -M12·M22 ]
        [ M21²        -2·M21·M22     M22²     ]
    """
    m11, m12 = float(M2[0, 0]), float(M2[0, 1])
    m21, m22 = float(M2[1, 0]), float(M2[1, 1])
    return np.array([
        [ m11**2,          -2*m11*m12,          m12**2   ],
        [-m21*m11,  m11*m22 + m12*m21,          -m12*m22  ],
        [ m21**2,          -2*m21*m22,           m22**2   ],
    ])


def _disp_vec_from_R6(M6: np.ndarray) -> np.ndarray:
    """Extract dispersion vector [R16, R26, R36, R46, R56] from 6×6 matrix."""
    return M6[[0, 1, 2, 3, 4], 5]   # shape (5,)


class Matrix3x3Widget(QWidget):
    """3×3 painted matrix for Twiss transport display."""

    CELL_W = 72
    CELL_H = 26

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QGridLayout(self)
        lay.setSpacing(1)
        lay.setContentsMargins(0, 0, 0, 0)

        labels = ["β", "α", "γ"]
        # col headers
        for c, lbl in enumerate(["β₀", "α₀", "γ₀"]):
            l = QLabel(lbl); l.setAlignment(Qt.AlignCenter)
            l.setFixedSize(self.CELL_W, 14)
            l.setStyleSheet("color:%s; font-size:8px; background:transparent;" % theme.FG_LBL)
            lay.addWidget(l, 0, c + 1)
        # row headers + cells
        self._cells: list[list[MatrixCell]] = []
        for r, rl in enumerate(["β₁", "α₁", "γ₁"]):
            lbl = QLabel(rl); lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            lbl.setFixedSize(22, self.CELL_H)
            lbl.setStyleSheet("color:%s; font-size:8px; background:transparent;" % theme.FG_LBL)
            lay.addWidget(lbl, r + 1, 0)
            row_cells = []
            for c in range(3):
                cell = MatrixCell(); cell.setFixedSize(self.CELL_W, self.CELL_H)
                lay.addWidget(cell, r + 1, c + 1)
                row_cells.append(cell)
            self._cells.append(row_cells)

    def set_matrix(self, T3: np.ndarray):
        max_abs = max(float(np.abs(T3).max()), 1e-14)
        for r in range(3):
            for c in range(3):
                self._cells[r][c].set_val(float(T3[r, c]), max_abs)

    def clear(self):
        for row in self._cells:
            for cell in row: cell.clear()


class DispVecWidget(QWidget):
    """Labeled column vector [R16, R26, R36, R46, R56]."""

    LABELS = ["R₁₆  (Dx)",  "R₂₆  (Dx')",
              "R₃₆  (Dy)",  "R₄₆  (Dy')", "R₅₆"]

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(2)

        t = QLabel(title)
        t.setStyleSheet("color:%s; font-size:%dpx; font-weight:bold; background:transparent;"
                        % (theme.FG_LBL, theme.FONT_TINY))
        lay.addWidget(t)

        self._rows: list[tuple[QLabel, QLabel]] = []
        for lbl_txt in self.LABELS:
            row = QHBoxLayout(); row.setSpacing(6); row.setContentsMargins(0,0,0,0)
            lbl = QLabel(lbl_txt); lbl.setFixedWidth(90)
            lbl.setStyleSheet("color:%s; font-size:%dpx; background:transparent;"
                              % (theme.FG_LBL, theme.FONT_TINY))
            val = QLabel("—"); val.setFixedWidth(90)
            val.setStyleSheet("color:%s; font-size:%dpx; font-family:monospace;"
                              " background:transparent; font-weight:bold;"
                              % (theme.FG, theme.FONT_SMALL))
            row.addWidget(lbl); row.addWidget(val); row.addStretch()
            lay.addLayout(row)
            self._rows.append((lbl, val))
        lay.addStretch()

    def set_vector(self, v: np.ndarray):
        max_abs = max(float(np.abs(v).max()), 1e-14)
        for i, (_, val_lbl) in enumerate(self._rows):
            x = float(v[i])
            frac = min(abs(x) / max_abs, 1.0)
            ri = int(0x1E + frac * (0xFD - 0x1E))
            gi = int(0x3A + frac * (0xA7 - 0x3A))
            bi = int(0x30 + frac * (0x69 - 0x30))
            col = f"#{ri:02x}{gi:02x}{bi:02x}" if abs(x) > max_abs * 0.001 else theme.FG_LBL
            val_lbl.setText(f"{x:+.5f}")
            val_lbl.setStyleSheet(
                "color:%s; font-size:%dpx; font-family:monospace; "
                "background:transparent; font-weight:bold;" % (col, theme.FONT_SMALL))

    def clear(self):
        for _, val_lbl in self._rows:
            val_lbl.setText("—")
            val_lbl.setStyleSheet(
                "color:%s; font-size:%dpx; font-family:monospace; "
                "background:transparent;" % (theme.FG_LBL, theme.FONT_SMALL))

COORD_NAMES = {
    "elegant": ["x", "x'", "y", "y'", "t", "δ"],
    "bmad":    ["x", "px", "y", "py", "z", "pz"],
}

class MatrixPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._result: LatticeResult | None = None
        self._selected_uid: str | None = None
        self._selected_idx: int | None = None
        self._convention: str = "elegant"

        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 6, 6, 6)
        outer.setSpacing(5)

        # Convention switcher
        conv_row = QHBoxLayout()
        conv_lbl = QLabel("Convention:")
        conv_lbl.setStyleSheet(
            f"color:{theme.FG_LBL}; font-size:{theme.FONT_TINY}px; background:transparent;")
        self._conv_combo = QComboBox()
        self._conv_combo.addItems([
            "ELEGANT / MAD-X  (x, x', y, y', t, δ)",
            "Bmad  (x, px, y, py, z, pz)"])
        self._conv_combo.setStyleSheet(f"""
            QComboBox {{
                background:{theme.MANTLE}; color:{theme.FG};
                border:1px solid {theme.BORDER}; border-radius:3px;
                padding:2px 6px; font-size:{theme.FONT_TINY}px;
            }}
            QComboBox QAbstractItemView {{
                background:{theme.PANEL}; color:{theme.FG};
                selection-background-color:{theme.ACCENT};
                selection-color:{theme.CRUST};
            }}
        """)
        self._conv_combo.currentIndexChanged.connect(self._on_conv_changed)
        conv_row.addWidget(conv_lbl)
        conv_row.addWidget(self._conv_combo, 1)
        outer.addLayout(conv_row)

        # Tabs
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                background:{theme.PANEL}; border:1px solid {theme.BORDER}; border-radius:4px;
            }}
            QTabBar::tab {{
                background:{theme.MANTLE}; color:{theme.FG_DIM};
                border:1px solid {theme.BORDER}; border-bottom:none;
                padding:3px 10px; font-size:{theme.FONT_TINY}px;
                border-top-left-radius:4px; border-top-right-radius:4px;
            }}
            QTabBar::tab:selected {{
                background:{theme.ACCENT}; color:{theme.CRUST}; font-weight:bold;
            }}
            QTabBar::tab:hover:!selected {{
                background:{theme.SURFACE2}; color:{theme.FG};
            }}
        """)

        # ── Tab 1: R total ────────────────────────────────────────
        tab_r = QWidget()
        tr_lay = QVBoxLayout(tab_r)
        tr_lay.setContentsMargins(4, 4, 4, 4)
        tr_lay.setSpacing(4)
        tr_lay.addWidget(_hdr("R  TOTAL"))

        self._grid_total = Matrix6x6Widget()
        self._grid_total.set_coord_labels(COORD_NAMES[self._convention])
        tr_lay.addWidget(self._grid_total)
        tr_lay.addWidget(_sep())

        stats_row = QHBoxLayout()
        self._stat_trx = StatBadge("Tr(Rx)")
        self._stat_try = StatBadge("Tr(Ry)")
        self._stat_det = StatBadge("det(R)")
        self._stat_r56 = StatBadge("R₅₆")
        for w in [self._stat_trx, self._stat_try, self._stat_det, self._stat_r56]:
            stats_row.addWidget(w)
        tr_lay.addLayout(stats_row)

        tune_row = QHBoxLayout()
        self._stat_qx = StatBadge("Qx")
        self._stat_qy = StatBadge("Qy")
        tune_row.addWidget(self._stat_qx)
        tune_row.addWidget(self._stat_qy)
        tr_lay.addLayout(tune_row)

        self._stab_lbl = QLabel("—")
        self._stab_lbl.setAlignment(Qt.AlignCenter)
        self._stab_lbl.setFixedHeight(24)
        self._stab_lbl.setStyleSheet(
            f"background:{theme.MANTLE}; color:{theme.FG_DIM}; "
            f"border-radius:4px; font-weight:bold; font-size:{theme.FONT_TINY}px;")
        tr_lay.addWidget(self._stab_lbl)
        tr_lay.addStretch()
        self._tabs.addTab(tab_r, "R total")

        # ── Tab 2: Element R ──────────────────────────────────────
        tab_elem = QWidget()
        te_lay = QVBoxLayout(tab_elem)
        te_lay.setContentsMargins(4, 4, 4, 4)
        te_lay.setSpacing(4)

        self._elem_lbl = QLabel("← click an element block")
        self._elem_lbl.setStyleSheet(
            f"color:{theme.FG_LBL}; font-size:{theme.FONT_TINY}px; background:transparent;")
        te_lay.addWidget(self._elem_lbl)

        te_lay.addWidget(_hdr("ELEMENT  R"))
        self._grid_elem = Matrix6x6Widget()
        self._grid_elem.set_coord_labels(COORD_NAMES[self._convention])
        te_lay.addWidget(self._grid_elem)

        te_lay.addWidget(_hdr("CUMULATIVE  R  (entrance → exit)"))
        self._grid_cumul = Matrix6x6Widget()
        self._grid_cumul.set_coord_labels(COORD_NAMES[self._convention])
        te_lay.addWidget(self._grid_cumul)
        te_lay.addStretch()
        self._tabs.addTab(tab_elem, "Element R")

        # ── Tab 3: T tensor ───────────────────────────────────────
        tab_T = QWidget()
        tT_lay = QVBoxLayout(tab_T)
        tT_lay.setContentsMargins(4, 4, 4, 4)
        tT_lay.setSpacing(4)
        tT_lay.addWidget(_hdr("T TENSOR  (2nd order)"))
        self._t_panel = TTensorPanel()
        tT_lay.addWidget(self._t_panel, 1)
        self._tabs.addTab(tab_T, "T tensor")

        # ── Tab 4: Twiss Transport ────────────────────────────────
        tab_tw = QWidget()
        ttw_lay = QVBoxLayout(tab_tw)
        ttw_lay.setContentsMargins(4, 4, 4, 4)
        ttw_lay.setSpacing(6)
        ttw_lay.addWidget(_hdr("TWISS TRANSPORT  3×3  (x-plane)"))
        tw_row1 = QHBoxLayout(); tw_row1.setSpacing(12)
        self._tw3_total_x  = Matrix3x3Widget()
        self._tw3_elem_x   = Matrix3x3Widget()
        self._tw3_cumul_x  = Matrix3x3Widget()
        for w, lbl in [(self._tw3_total_x, "Total"),
                       (self._tw3_elem_x,  "Element"),
                       (self._tw3_cumul_x, "Cumulative")]:
            col = QVBoxLayout(); col.setSpacing(2)
            col.addWidget(QLabel(lbl, styleSheet=f"color:{theme.FG_LBL};font-size:{theme.FONT_TINY}px;background:transparent;"))
            col.addWidget(w); tw_row1.addLayout(col)
        tw_row1.addStretch(); ttw_lay.addLayout(tw_row1)
        ttw_lay.addWidget(_hdr("TWISS TRANSPORT  3×3  (y-plane)"))
        tw_row2 = QHBoxLayout(); tw_row2.setSpacing(12)
        self._tw3_total_y  = Matrix3x3Widget()
        self._tw3_elem_y   = Matrix3x3Widget()
        self._tw3_cumul_y  = Matrix3x3Widget()
        for w, lbl in [(self._tw3_total_y, "Total"),
                       (self._tw3_elem_y,  "Element"),
                       (self._tw3_cumul_y, "Cumulative")]:
            col = QVBoxLayout(); col.setSpacing(2)
            col.addWidget(QLabel(lbl, styleSheet=f"color:{theme.FG_LBL};font-size:{theme.FONT_TINY}px;background:transparent;"))
            col.addWidget(w); tw_row2.addLayout(col)
        tw_row2.addStretch(); ttw_lay.addLayout(tw_row2)
        ttw_lay.addStretch()
        self._tabs.addTab(tab_tw, "Twiss 3×3")

        # ── Tab 5: Dispersion Vector ──────────────────────────────
        tab_dv = QWidget()
        tdv_lay = QVBoxLayout(tab_dv)
        tdv_lay.setContentsMargins(4, 4, 4, 4)
        tdv_lay.setSpacing(6)
        tdv_lay.addWidget(_hdr("DISPERSION VECTOR  [R₁₆, R₂₆, R₃₆, R₄₆, R₅₆]"))
        dv_row = QHBoxLayout(); dv_row.setSpacing(20)
        self._dv_total  = DispVecWidget("Total  (entrance → exit)")
        self._dv_elem   = DispVecWidget("Element  (element only)")
        self._dv_cumul  = DispVecWidget("Cumulative  (entrance → here)")
        dv_row.addWidget(self._dv_total)
        dv_row.addWidget(self._dv_elem)
        dv_row.addWidget(self._dv_cumul)
        dv_row.addStretch(); tdv_lay.addLayout(dv_row)
        tdv_lay.addStretch()
        self._tabs.addTab(tab_dv, "Dispersion")

        outer.addWidget(self._tabs, 1)

    # ── Convention ─────────────────────────────────────────────────

    def _on_conv_changed(self, idx: int):
        self._convention = "bmad" if idx == 1 else "elegant"
        names = COORD_NAMES[self._convention]
        self._grid_total.set_coord_labels(names)
        self._grid_elem.set_coord_labels(names)
        self._grid_cumul.set_coord_labels(names)
        if self._result:
            self._show_total()
            if self._selected_idx is not None:
                self._show_element()

    def _conv(self, M: np.ndarray) -> np.ndarray:
        return to_bmad(M) if self._convention == "bmad" else M

    # ── Public API ──────────────────────────────────────────────────

    def update_result(self, result: LatticeResult):
        self._result = result
        self._show_total()
        self._t_panel.set_T(result.T)
        if self._selected_idx is not None:
            self._show_element()

    def set_selected_element(self, uid: str | None, idx: int | None,
                             name: str = ""):
        self._selected_uid = uid
        self._selected_idx = idx
        if uid is None or idx is None:
            self._elem_lbl.setText("← click an element block")
            self._grid_elem.clear()
            self._grid_cumul.clear()
        else:
            self._elem_lbl.setText(f"[{idx + 1}]  {name}")
            self._show_element()
        if uid is not None:
            self._tabs.setCurrentIndex(1)

    # ── Internal ────────────────────────────────────────────────────

    def _show_total(self):
        if self._result is None:
            return
        R = self._result.R
        self._grid_total.set_matrix(self._conv(R))
        # Twiss 3×3 total
        self._tw3_total_x.set_matrix(_twiss3_from_R2(R[:2, :2]))
        self._tw3_total_y.set_matrix(_twiss3_from_R2(R[2:4, 2:4]))
        # Dispersion vector total
        self._dv_total.set_vector(_disp_vec_from_R6(R))

        trx     = self._result.trace_x
        try_val = self._result.trace_y
        det     = float(np.linalg.det(self._result.R))
        r56     = float(self._result.R[4, 5])

        self._stat_trx.set(f"{trx:+.5f}",
            theme.SUCCESS if abs(trx) < 2 else theme.ERROR)
        self._stat_try.set(f"{try_val:+.5f}",
            theme.SUCCESS if abs(try_val) < 2 else theme.ERROR)
        det_err = abs(det - 1.0)
        self._stat_det.set(f"{det:+.5f}",
            theme.SUCCESS if det_err < 1e-5 else
            theme.WARN    if det_err < 1e-3 else theme.ERROR)
        self._stat_r56.set(f"{r56:+.5f}", theme.COLOR_DISP)

        if self._result.Qx is not None:
            self._stat_qx.set(f"{self._result.Qx:.5f}", theme.TWISS_A)
        else:
            self._stat_qx.set("— (linac)")
        if self._result.Qy is not None:
            self._stat_qy.set(f"{self._result.Qy:.5f}", theme.TWISS_B)
        else:
            self._stat_qy.set("— (linac)")

        trx_ok = abs(trx) < 2
        try_ok = abs(try_val) < 2
        if trx_ok and try_ok:
            txt = f"✓ STABLE  |Trx|={abs(trx):.3f}  |Try|={abs(try_val):.3f}"
            self._stab_lbl.setStyleSheet(
                f"background:{theme.SUCCESS}22; color:{theme.SUCCESS}; "
                f"border:1px solid {theme.SUCCESS}; border-radius:4px; "
                f"font-weight:bold; font-size:{theme.FONT_TINY}px; padding:2px;")
        else:
            txt = f"✗ UNSTABLE  |Trx|={abs(trx):.3f}  |Try|={abs(try_val):.3f}"
            self._stab_lbl.setStyleSheet(
                f"background:{theme.ERROR}22; color:{theme.ERROR}; "
                f"border:1px solid {theme.ERROR}; border-radius:4px; "
                f"font-weight:bold; font-size:{theme.FONT_TINY}px; padding:2px;")
        self._stab_lbl.setText(txt)

    def _show_element(self):
        if self._result is None or self._selected_idx is None:
            return
        idx = self._selected_idx
        if idx >= len(self._result.R_each):
            return
        Re   = self._result.R_each[idx]
        Rcum = self._result.R_cumul[idx + 1]
        self._grid_elem.set_matrix(self._conv(Re))
        self._grid_cumul.set_matrix(self._conv(Rcum))
        # Twiss 3×3 element + cumulative
        self._tw3_elem_x.set_matrix(_twiss3_from_R2(Re[:2, :2]))
        self._tw3_elem_y.set_matrix(_twiss3_from_R2(Re[2:4, 2:4]))
        self._tw3_cumul_x.set_matrix(_twiss3_from_R2(Rcum[:2, :2]))
        self._tw3_cumul_y.set_matrix(_twiss3_from_R2(Rcum[2:4, 2:4]))
        # Dispersion vector element + cumulative
        self._dv_elem.set_vector(_disp_vec_from_R6(Re))
        self._dv_cumul.set_vector(_disp_vec_from_R6(Rcum))
