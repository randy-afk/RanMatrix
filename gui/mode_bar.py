"""
gui/mode_bar.py
---------------
Compact toolbar widget:  [Linac | Ring]  [Linear | Nonlinear]
Emits signals on change.
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QFrame
import theme


class ToggleGroup(QWidget):
    """Exclusive two-button toggle."""
    changed = Signal(str)

    def __init__(self, label: str, options: list[str], parent=None):
        super().__init__(parent)
        self._options = options
        self._current = options[0]

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        lbl = QLabel(f"  {label}: ")
        lbl.setStyleSheet(f"color:{theme.FG_LBL}; font-size:{theme.FONT_SMALL}px;")
        layout.addWidget(lbl)

        self._buttons: dict[str, QPushButton] = {}
        for i, opt in enumerate(options):
            btn = QPushButton(opt)
            btn.setCheckable(True)
            btn.setFixedHeight(26)
            btn.setFixedWidth(90)
            # Round left edge only for first, right only for last
            radius_left  = "5px" if i == 0 else "0"
            radius_right = "5px" if i == len(options) - 1 else "0"
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {theme.MANTLE};
                    color: {theme.FG_DIM};
                    border: 1px solid {theme.BORDER};
                    border-radius: 0;
                    border-top-left-radius: {radius_left};
                    border-bottom-left-radius: {radius_left};
                    border-top-right-radius: {radius_right};
                    border-bottom-right-radius: {radius_right};
                    font-size: {theme.FONT_SMALL}px;
                    padding: 0 8px;
                }}
                QPushButton:checked {{
                    background: {theme.ACCENT};
                    color: {theme.CRUST};
                    border-color: {theme.ACCENT};
                    font-weight: bold;
                }}
                QPushButton:hover:!checked {{
                    background: {theme.SURFACE2};
                    color: {theme.FG};
                }}
            """)
            btn.clicked.connect(lambda checked, o=opt: self._select(o))
            layout.addWidget(btn)
            self._buttons[opt] = btn

        self._buttons[options[0]].setChecked(True)

    def _select(self, option: str):
        if option == self._current:
            # Re-check the active button (don't allow deselect)
            self._buttons[option].setChecked(True)
            return
        self._current = option
        for opt, btn in self._buttons.items():
            btn.setChecked(opt == option)
        self.changed.emit(option)

    def set_value(self, option: str):
        self._select(option)

    @property
    def value(self) -> str:
        return self._current


class ModeBar(QWidget):
    """Toolbar segment with Linac/Ring + Linear/Nonlinear toggles."""
    mode_changed   = Signal(str)    # "linac" or "ring"
    linear_changed = Signal(bool)   # True = linear

    def __init__(self, lattice, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(16)

        self._mode_toggle   = ToggleGroup("Mode",     ["Linac", "Ring"])
        self._linear_toggle = ToggleGroup("Physics",  ["Linear", "Nonlinear"])

        layout.addWidget(self._mode_toggle)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet(f"color:{theme.BORDER};")
        layout.addWidget(sep)

        layout.addWidget(self._linear_toggle)

        self._mode_toggle.changed.connect(
            lambda v: self.mode_changed.emit(v.lower())
        )
        self._linear_toggle.changed.connect(
            lambda v: self.linear_changed.emit(v == "Linear")
        )

    def set_state(self, lattice):
        self._mode_toggle.set_value("Ring" if lattice.mode == "ring" else "Linac")
        self._linear_toggle.set_value("Linear" if lattice.linear else "Nonlinear")
