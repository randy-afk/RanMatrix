"""
gui/twiss_panel.py — both planes, Qx/Qy, dispersion both planes.
"""
from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
import theme
from models.lattice import LatticeResult


def _hdr(text):
    lbl = QLabel(text)
    lbl.setObjectName("twissHdr")
    lbl.setStyleSheet(
        f"QLabel#twissHdr {{background:{theme.ACCENT}; color:{theme.CRUST};"
        f"font-size:{theme.FONT_SMALL}px; font-weight:bold; letter-spacing:1px;"
        f"padding:3px 10px; border-radius:4px;}}")
    return lbl


def _sep():
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    f.setFixedHeight(1)
    f.setStyleSheet(f"background:{theme.BORDER};")
    return f


class SB(QWidget):
    """Stat block: label above, bold value below. Clean transparent internals."""

    def __init__(self, label: str, unit: str = "", parent=None):
        super().__init__(parent)
        # Only the outer container gets the MANTLE background
        self.setStyleSheet(
            f"SB {{ background:{theme.MANTLE}; border-radius:4px; }}"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 3, 6, 4)
        lay.setSpacing(1)

        # Label row — transparent so MANTLE shows through
        top = QHBoxLayout()
        top.setSpacing(2)
        top.setContentsMargins(0, 0, 0, 0)

        lbl_text = f"{label}  {unit}".strip() if unit else label
        lbl = QLabel(lbl_text)
        lbl.setStyleSheet(
            f"background:transparent; color:{theme.FG_LBL}; "
            f"font-size:{theme.FONT_TINY}px;")
        top.addWidget(lbl)
        top.addStretch()
        lay.addLayout(top)

        self._v = QLabel("—")
        self._v.setStyleSheet(
            f"background:transparent; color:{theme.FG}; "
            f"font-size:{theme.FONT_SMALL}px; font-weight:bold; font-family:monospace;")
        lay.addWidget(self._v)

    def set(self, text: str, color: str = None):
        self._v.setText(text)
        c = color or theme.FG
        self._v.setStyleSheet(
            f"background:transparent; color:{c}; "
            f"font-size:{theme.FONT_SMALL}px; font-weight:bold; font-family:monospace;")


class TwissPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(5)

        # Tunes
        lay.addWidget(_hdr("TUNES"))
        tune_row = QHBoxLayout(); tune_row.setSpacing(4)
        self._qx = SB("Qx"); self._qy = SB("Qy")
        tune_row.addWidget(self._qx); tune_row.addWidget(self._qy)
        lay.addLayout(tune_row)

        lay.addWidget(_sep())
        lay.addWidget(_hdr("X PLANE"))

        r1 = QHBoxLayout(); r1.setSpacing(4)
        self._bx_in  = SB("βx in",  "m"); self._bx_out = SB("βx out", "m")
        r1.addWidget(self._bx_in); r1.addWidget(self._bx_out); lay.addLayout(r1)

        r2 = QHBoxLayout(); r2.setSpacing(4)
        self._ax_in  = SB("αx in"); self._ax_out = SB("αx out")
        r2.addWidget(self._ax_in); r2.addWidget(self._ax_out); lay.addLayout(r2)

        r3 = QHBoxLayout(); r3.setSpacing(4)
        self._phix = SB("Δφx", "rad"); self._dx_out = SB("Dx out", "m")
        r3.addWidget(self._phix); r3.addWidget(self._dx_out); lay.addLayout(r3)

        lay.addWidget(_sep())
        lay.addWidget(_hdr("Y PLANE"))

        r4 = QHBoxLayout(); r4.setSpacing(4)
        self._by_in  = SB("βy in",  "m"); self._by_out = SB("βy out", "m")
        r4.addWidget(self._by_in); r4.addWidget(self._by_out); lay.addLayout(r4)

        r5 = QHBoxLayout(); r5.setSpacing(4)
        self._ay_in  = SB("αy in"); self._ay_out = SB("αy out")
        r5.addWidget(self._ay_in); r5.addWidget(self._ay_out); lay.addLayout(r5)

        r6 = QHBoxLayout(); r6.setSpacing(4)
        self._phiy = SB("Δφy", "rad"); self._dy_out = SB("Dy out", "m")
        r6.addWidget(self._phiy); r6.addWidget(self._dy_out); lay.addLayout(r6)

        lay.addWidget(_sep())
        lay.addWidget(_hdr("LONGITUDINAL"))
        r7 = QHBoxLayout(); r7.setSpacing(4)
        self._r56 = SB("R₅₆", "m")
        self._r56.setToolTip("Path length momentum compaction")
        r7.addWidget(self._r56)
        lay.addLayout(r7)
        lay.addStretch()

    def update_result(self, result: LatticeResult):
        tp = result.twiss_points
        if not tp:
            return
        t0, t1 = tp[0], tp[-1]

        self._qx.set(f"{result.Qx:.5f}" if result.Qx is not None else "— linac",
                     theme.TWISS_A if result.Qx is not None else theme.FG_LBL)
        self._qy.set(f"{result.Qy:.5f}" if result.Qy is not None else "— linac",
                     theme.TWISS_B if result.Qy is not None else theme.FG_LBL)

        self._bx_in.set(f"{t0.betax:.4f}",  theme.TWISS_A)
        self._bx_out.set(f"{t1.betax:.4f}", theme.TWISS_A)
        self._ax_in.set(f"{t0.alphax:+.4f}")
        self._ax_out.set(f"{t1.alphax:+.4f}")
        self._phix.set(f"{t1.phix - t0.phix:.4f}")
        self._dx_out.set(f"{t1.Dx:.4f}", theme.COLOR_DISP)

        self._by_in.set(f"{t0.betay:.4f}",  theme.TWISS_B)
        self._by_out.set(f"{t1.betay:.4f}", theme.TWISS_B)
        self._ay_in.set(f"{t0.alphay:+.4f}")
        self._ay_out.set(f"{t1.alphay:+.4f}")
        self._phiy.set(f"{t1.phiy - t0.phiy:.4f}")
        self._dy_out.set(f"{t1.Dy:.4f}", theme.COLOR_DISP)

        self._r56.set(f"{t1.R56_cum:+.4f}")
