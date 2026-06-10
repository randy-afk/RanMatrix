"""
gui/palette_panel.py
--------------------
Left panel: element type buttons grouped by category.
Click → emits element_requested(ElementType).
"""

from __future__ import annotations
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy, QLineEdit
)
import theme
from models.element import ElementType, ELEMENT_META, ELEM_SOLENOID


PALETTE_GROUPS = [
    ("Basic", [
        ElementType.DRIFT,
        ElementType.QUAD_F,
        ElementType.QUAD_D,
        ElementType.DIPOLE_SECTOR,
        ElementType.DIPOLE_RECT,
        ElementType.SOLENOID,
    ]),
    ("Higher Order", [
        ElementType.SEXTUPOLE,
        ElementType.OCTUPOLE,
        ElementType.THIN_MULTIPOLE,
    ]),
    ("RF / Corrections", [
        ElementType.RF_CAVITY,
        ElementType.H_KICKER,
        ElementType.V_KICKER,
    ]),
    ("Apertures", [
        ElementType.APERTURE_CIRC,
        ElementType.APERTURE_RECT,
    ]),
    ("Special", [
        ElementType.MISALIGN,
        ElementType.MARKER,
    ]),
]


class ElementButton(QPushButton):
    """A single element in the palette."""

    clicked_type = Signal(object)   # ElementType

    def __init__(self, etype: ElementType, parent=None):
        meta = ELEMENT_META[etype]
        label = meta["label"]
        abbrev = meta["abbrev"]
        color = meta["color"]
        super().__init__(f"[{abbrev}]  {label}", parent)
        self._etype = etype
        self._color = color

        self.setToolTip(self._build_tooltip(etype, meta))
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(30)

        self._apply_style(False)
        self.clicked.connect(lambda: self.clicked_type.emit(self._etype))

    def _apply_style(self, hovered: bool):
        bg = self._color if hovered else theme.PANEL
        fg = theme.CRUST if hovered else theme.FG
        border = self._color
        self.setStyleSheet(f"""
            QPushButton {{
                background: {bg};
                color: {fg};
                border: 1px solid {border};
                border-left: 4px solid {border};
                border-radius: 4px;
                text-align: left;
                padding-left: 8px;
                font-size: {theme.FONT_SMALL}px;
            }}
            QPushButton:hover {{
                background: {self._color};
                color: {theme.CRUST};
            }}
            QPushButton:pressed {{
                background: {self._color}cc;
                color: {theme.CRUST};
            }}
        """)

    @staticmethod
    def _build_tooltip(etype: ElementType, meta: dict) -> str:
        specs = meta["params"]
        if not specs:
            return f"{meta['label']} — no parameters"
        lines = [f"<b>{meta['label']}</b>", "<br>Parameters:"]
        for s in specs:
            lines.append(f"  {s.label} [{s.unit}]" if s.unit else f"  {s.label}")
        return "\n".join(lines)


class CategoryHeader(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text.upper(), parent)
        self.setStyleSheet(f"""
            QLabel {{
                color: {theme.CRUST};
                background: {theme.ACCENT};
                font-size: {theme.FONT_TINY}px;
                font-weight: bold;
                letter-spacing: 1px;
                padding: 3px 8px;
                border-radius: 3px;
            }}
        """)


class PalettePanel(QWidget):
    element_requested = Signal(object)   # ElementType

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(180)
        self.setMaximumWidth(240)
        self.setStyleSheet(f"background:{theme.PANEL};")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 6, 6, 6)
        outer.setSpacing(4)

        # Search bar
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search elements…")
        self._search.setStyleSheet(f"""
            QLineEdit {{
                background: {theme.MANTLE};
                color: {theme.FG};
                border: 1px solid {theme.BORDER};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: {theme.FONT_SMALL}px;
            }}
            QLineEdit:focus {{
                border-color: {theme.ACCENT};
            }}
        """)
        self._search.textChanged.connect(self._on_search)
        outer.addWidget(self._search)

        # Scrollable button area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        outer.addWidget(scroll)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self._container_layout = QVBoxLayout(container)
        self._container_layout.setContentsMargins(0, 0, 0, 0)
        self._container_layout.setSpacing(3)
        scroll.setWidget(container)

        # Build button groups
        self._all_buttons: list[tuple[ElementType, ElementButton]] = []
        self._group_headers: list[tuple[QLabel, list[ElementButton]]] = []

        for category, etypes in PALETTE_GROUPS:
            hdr = CategoryHeader(category)
            self._container_layout.addWidget(hdr)
            btns = []
            for etype in etypes:
                btn = ElementButton(etype)
                btn.clicked_type.connect(self.element_requested.emit)
                self._container_layout.addWidget(btn)
                self._all_buttons.append((etype, btn))
                btns.append(btn)
            self._group_headers.append((hdr, btns))
            spacer_line = QFrame()
            spacer_line.setFixedHeight(1)
            spacer_line.setStyleSheet(f"background:{theme.BORDER};")
            self._container_layout.addWidget(spacer_line)

        self._container_layout.addStretch()

    def _on_search(self, text: str):
        text = text.strip().lower()
        for category_hdr, btns in self._group_headers:
            any_visible = False
            for btn in btns:
                visible = (not text or
                           text in btn.text().lower() or
                           text in btn._etype.value.lower())
                btn.setVisible(visible)
                if visible:
                    any_visible = True
            category_hdr.setVisible(any_visible)
