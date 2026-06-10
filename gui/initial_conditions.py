"""
gui/initial_conditions.py
--------------------------
Panel for editing initial beam conditions:
  - Twiss: βx₀, αx₀, βy₀, αy₀  (greyed out in ring mode)
  - Dispersion: Dx₀, Dx'₀, Dy₀, Dy'₀
  - Single particle: x₀, x'₀, y₀, y'₀
  - Emittance: εx, εy

In ring mode, Twiss and dispersion are locked (periodic solution).
Emittance and particle initial conditions are always editable.
"""

from __future__ import annotations
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QDoubleSpinBox, QFrame, QGridLayout
)
import theme


def _hdr(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("icHdr")
    lbl.setStyleSheet(
        f"QLabel#icHdr {{background:{theme.ACCENT}; color:{theme.CRUST}; "
        f"font-size:{theme.FONT_SMALL}px; font-weight:bold; "
        f"padding:2px 8px; border-radius:3px; letter-spacing:1px;}}")
    return lbl


def _sep() -> QFrame:
    f = QFrame(); f.setFrameShape(QFrame.HLine)
    f.setFixedHeight(1)
    f.setStyleSheet(f"background:{theme.BORDER};")
    return f


class SpinField(QWidget):
    """Label + spinbox + unit, emits changed(value)."""
    changed = Signal(float)

    def __init__(self, label: str, value: float,
                 lo: float = -1e9, hi: float = 1e9,
                 decimals: int = 6, unit: str = "",
                 parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        lbl = QLabel(label)
        lbl.setFixedWidth(52)
        lbl.setStyleSheet(
            f"color:{theme.FG_LBL}; font-size:{theme.FONT_SMALL}px; "
            f"background:transparent;")
        lay.addWidget(lbl)

        self._spin = QDoubleSpinBox()
        self._spin.setDecimals(decimals)
        self._spin.setRange(lo, hi)
        self._spin.setValue(value)
        self._spin.setStyleSheet(f"""
            QDoubleSpinBox {{
                background:{theme.MANTLE}; color:{theme.FG};
                border:1px solid {theme.BORDER}; border-radius:3px;
                padding:2px 4px; font-size:{theme.FONT_SMALL}px;
            }}
            QDoubleSpinBox:focus {{ border-color:{theme.ACCENT}; }}
            QDoubleSpinBox:disabled {{
                background:{theme.CRUST}; color:{theme.FG_LBL};
                border-color:{theme.CRUST};
            }}
        """)
        self._spin.valueChanged.connect(self.changed.emit)
        lay.addWidget(self._spin, 1)

        if unit:
            u = QLabel(unit)
            u.setFixedWidth(36)
            u.setStyleSheet(
                f"color:{theme.FG_LBL}; font-size:{theme.FONT_TINY}px; "
                f"background:transparent;")
            lay.addWidget(u)

    def value(self) -> float:
        return self._spin.value()

    def set_value(self, v: float):
        self._spin.blockSignals(True)
        self._spin.setValue(v)
        self._spin.blockSignals(False)

    def set_enabled(self, en: bool):
        self._spin.setEnabled(en)


class InitialConditionsPanel(QWidget):
    """Emits conditions_changed whenever any field is edited."""

    conditions_changed = Signal(dict)   # full dict of all initial conditions

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ring_mode = False

        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(6)

        # ── Ring mode note ─────────────────────────────────────────
        self._ring_note = QLabel(
            "⟳  Ring mode — Twiss & dispersion computed from periodic solution")
        self._ring_note.setWordWrap(True)
        self._ring_note.setStyleSheet(
            f"color:{theme.ACCENT}; font-size:{theme.FONT_TINY}px; "
            f"background:transparent; font-style:italic;")
        self._ring_note.setVisible(False)
        lay.addWidget(self._ring_note)

        # ── Twiss ─────────────────────────────────────────────────
        lay.addWidget(_hdr("TWISS  (entrance)"))
        twiss_grid = QGridLayout()
        twiss_grid.setSpacing(4)

        self._bx = SpinField("βx₀", 1.0, 0.001, 1e6, 6, "m")
        self._ax = SpinField("αx₀", 0.0, -100, 100, 6, "")
        self._by = SpinField("βy₀", 1.0, 0.001, 1e6, 6, "m")
        self._ay = SpinField("αy₀", 0.0, -100, 100, 6, "")

        twiss_grid.addWidget(self._bx, 0, 0)
        twiss_grid.addWidget(self._ax, 0, 1)
        twiss_grid.addWidget(self._by, 1, 0)
        twiss_grid.addWidget(self._ay, 1, 1)
        lay.addLayout(twiss_grid)

        # ── Dispersion ────────────────────────────────────────────
        lay.addWidget(_sep())
        lay.addWidget(_hdr("DISPERSION  (entrance)"))
        disp_grid = QGridLayout()
        disp_grid.setSpacing(4)

        self._dx  = SpinField("Dx₀",  0.0, -100, 100, 6, "m")
        self._dxp = SpinField("Dx'₀", 0.0, -100, 100, 6, "rad")
        self._dy  = SpinField("Dy₀",  0.0, -100, 100, 6, "m")
        self._dyp = SpinField("Dy'₀", 0.0, -100, 100, 6, "rad")

        disp_grid.addWidget(self._dx,  0, 0)
        disp_grid.addWidget(self._dxp, 0, 1)
        disp_grid.addWidget(self._dy,  1, 0)
        disp_grid.addWidget(self._dyp, 1, 1)
        lay.addLayout(disp_grid)

        # ── Emittance ─────────────────────────────────────────────
        lay.addWidget(_sep())
        lay.addWidget(_hdr("EMITTANCE"))
        emit_grid = QGridLayout()
        emit_grid.setSpacing(4)

        self._ex = SpinField("εx", 1.0, 0, 1e6, 4, "mm·mrad")
        self._ey = SpinField("εy", 1.0, 0, 1e6, 4, "mm·mrad")
        emit_grid.addWidget(self._ex, 0, 0)
        emit_grid.addWidget(self._ey, 0, 1)
        lay.addLayout(emit_grid)

        # ── Single particle ───────────────────────────────────────
        lay.addWidget(_sep())
        lay.addWidget(_hdr("PARTICLE  (x, x', y, y')"))
        part_grid = QGridLayout()
        part_grid.setSpacing(4)

        self._x0  = SpinField("x₀",  1.0,  -1e4, 1e4, 4, "mm")
        self._xp0 = SpinField("x'₀", 0.0,  -1e4, 1e4, 4, "mrad")
        self._y0  = SpinField("y₀",  0.0,  -1e4, 1e4, 4, "mm")
        self._yp0 = SpinField("y'₀", 0.0,  -1e4, 1e4, 4, "mrad")

        part_grid.addWidget(self._x0,  0, 0)
        part_grid.addWidget(self._xp0, 0, 1)
        part_grid.addWidget(self._y0,  1, 0)
        part_grid.addWidget(self._yp0, 1, 1)
        lay.addLayout(part_grid)

        lay.addStretch()

        # Connect all fields
        for field in [self._bx, self._ax, self._by, self._ay,
                      self._dx, self._dxp, self._dy, self._dyp,
                      self._ex, self._ey,
                      self._x0, self._xp0, self._y0, self._yp0]:
            field.changed.connect(self._emit_conditions)

        # Store all Twiss/disp fields for locking
        self._twiss_fields = [self._bx, self._ax, self._by, self._ay,
                              self._dx, self._dxp, self._dy, self._dyp]

    # ── Public API ────────────────────────────────────────────────

    def set_mode(self, ring: bool):
        """Lock/unlock Twiss fields based on ring vs linac mode."""
        self._ring_mode = ring
        self._ring_note.setVisible(ring)
        for f in self._twiss_fields:
            f.set_enabled(not ring)

    def set_from_lattice(self, lattice):
        """Populate all fields from Lattice object (no signals)."""
        def _s(field, val):
            field.changed.disconnect(self._emit_conditions)
            field.set_value(val)
            field.changed.connect(self._emit_conditions)

        _s(self._bx,  lattice.betax0)
        _s(self._ax,  lattice.alphax0)
        _s(self._by,  lattice.betay0)
        _s(self._ay,  lattice.alphay0)
        _s(self._dx,  lattice.Dx0)
        _s(self._dxp, lattice.Dxp0)
        _s(self._dy,  lattice.Dy0)
        _s(self._dyp, lattice.Dyp0)
        _s(self._ex,  lattice.emittance_x * 1e6)
        _s(self._ey,  lattice.emittance_y * 1e6)
        _s(self._x0,  lattice.x0  * 1e3)
        _s(self._xp0, lattice.xp0 * 1e3)
        _s(self._y0,  lattice.y0  * 1e3)
        _s(self._yp0, lattice.yp0 * 1e3)

    def update_from_result(self, result, lattice):
        """
        In ring mode, update Twiss/dispersion fields from the
        periodic solution (read-only display update).
        """
        if not self._ring_mode:
            return
        tp0 = result.twiss_points[0]
        for field, val in [
            (self._bx,  tp0.betax),
            (self._ax,  tp0.alphax),
            (self._by,  tp0.betay),
            (self._ay,  tp0.alphay),
            (self._dx,  tp0.Dx),
            (self._dxp, tp0.Dxp),
            (self._dy,  tp0.Dy),
            (self._dyp, tp0.Dyp),
        ]:
            field.changed.disconnect(self._emit_conditions)
            field.set_value(val)
            field.changed.connect(self._emit_conditions)

    def get_conditions(self) -> dict:
        return {
            "betax0":      self._bx.value(),
            "alphax0":     self._ax.value(),
            "betay0":      self._by.value(),
            "alphay0":     self._ay.value(),
            "Dx0":         self._dx.value(),
            "Dxp0":        self._dxp.value(),
            "Dy0":         self._dy.value(),
            "Dyp0":        self._dyp.value(),
            "emittance_x": self._ex.value() * 1e-6,
            "emittance_y": self._ey.value() * 1e-6,
            "x0":          self._x0.value()  * 1e-3,
            "xp0":         self._xp0.value() * 1e-3,
            "y0":          self._y0.value()  * 1e-3,
            "yp0":         self._yp0.value() * 1e-3,
        }

    # ── Internal ──────────────────────────────────────────────────

    def _emit_conditions(self, _=None):
        if not self._ring_mode:
            self.conditions_changed.emit(self.get_conditions())
