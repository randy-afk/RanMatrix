"""
gui/lattice_line.py
-------------------
Horizontal scrollable strip of element blocks.
Each block is a coloured button with the element's abbreviation.
Supports:
  - Click → select (emits element_selected)
  - X button → remove (emits element_removed)
  - Drag-to-reorder (emits order_changed)
  - Hover tooltip showing element matrix
"""

from __future__ import annotations

from PySide6.QtCore import Signal, Qt, QMimeData, QPoint, QSize
from PySide6.QtGui import QDrag, QPixmap, QPainter, QColor, QFont, QPen
from PySide6.QtWidgets import (
    QWidget, QScrollArea, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QFrame, QToolButton
)
import theme
from models.element import Element, ELEMENT_META


BLOCK_W = 64
BLOCK_H = 64
REMOVE_SIZE = 16


class ElementBlock(QFrame):
    """One element tile in the lattice line."""

    selected        = Signal(str)   # uid — single click
    double_clicked  = Signal(str)   # uid — double click opens editor
    removed         = Signal(str)   # uid
    drag_started    = Signal(str)   # uid

    def __init__(self, element: Element, parent=None):
        super().__init__(parent)
        self._uid   = element.uid
        self._elem  = element
        self._color = element.color
        self._selected = False

        self.setFixedSize(BLOCK_W, BLOCK_H)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(self._make_tooltip(element))
        self._drag_start: QPoint | None = None
        self._apply_style()

    def set_selected(self, sel: bool):
        self._selected = sel
        self._apply_style()

    def _apply_style(self):
        border_color = theme.ACCENT if self._selected else self._color
        border_w = 3 if self._selected else 1
        self.setStyleSheet(f"""
            QFrame {{
                background: {self._color};
                border: {border_w}px solid {border_color};
                border-radius: 6px;
            }}
        """)
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Abbreviation
        abbrev = self._elem.abbrev
        label  = self._elem.label

        painter.setPen(QColor(theme.CRUST))
        f_abbrev = QFont("Segoe UI", 11, QFont.Bold)
        painter.setFont(f_abbrev)
        painter.drawText(self.rect().adjusted(0, 4, 0, -16), Qt.AlignHCenter | Qt.AlignTop, abbrev)

        painter.setPen(QColor(theme.CRUST + "cc"))
        f_label = QFont("Segoe UI", 7)
        painter.setFont(f_label)
        # Truncate long labels
        display = label if len(label) <= 8 else label[:7] + "…"
        painter.drawText(self.rect().adjusted(2, 0, -2, -2), Qt.AlignHCenter | Qt.AlignBottom, display)

        # Thin/thick badge
        if self._elem.thin:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(theme.CRUST + "99"))
            painter.drawRoundedRect(3, 3, 20, 11, 3, 3)
            painter.setPen(QColor(theme.FG))
            painter.setFont(QFont("Segoe UI", 6))
            painter.drawText(3, 3, 20, 11, Qt.AlignCenter, "thin")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start = event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            dist = (event.pos() - self._drag_start).manhattanLength() if self._drag_start else 100
            if dist < 5:
                self.selected.emit(self._uid)   # highlight only
        self._drag_start = None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.selected.emit(self._uid)
            self.double_clicked.emit(self._uid)

    def mouseMoveEvent(self, event):
        if self._drag_start is None:
            return
        if (event.pos() - self._drag_start).manhattanLength() < 10:
            return
        # Start drag
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(self._uid)
        drag.setMimeData(mime)
        # Drag pixmap
        pix = QPixmap(self.size())
        pix.fill(Qt.transparent)
        self.render(pix)
        drag.setPixmap(pix)
        drag.setHotSpot(event.pos())
        drag.exec(Qt.MoveAction)

    # ── Remove button (painted on hover via child widget) ────────

    def enterEvent(self, event):
        if not hasattr(self, "_rm_btn"):
            self._rm_btn = QToolButton(self)
            self._rm_btn.setText("✕")
            self._rm_btn.setFixedSize(REMOVE_SIZE, REMOVE_SIZE)
            self._rm_btn.move(BLOCK_W - REMOVE_SIZE - 2, 2)
            self._rm_btn.setStyleSheet(f"""
                QToolButton {{
                    background: {theme.ERROR};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 9px;
                    font-weight: bold;
                }}
                QToolButton:hover {{ background: #ff2222; }}
            """)
            self._rm_btn.clicked.connect(lambda: self.removed.emit(self._uid))
        self._rm_btn.show()

    def leaveEvent(self, event):
        if hasattr(self, "_rm_btn"):
            self._rm_btn.hide()

    @staticmethod
    def _make_tooltip(element: Element) -> str:
        try:
            M = element.matrix6()
        except Exception:
            M = None
        lines = [f"<b>{element.label}</b> ({element.etype.value})<br>"]
        if M is not None:
            lines.append("R matrix (x,x' block):<br>")
            lines.append(f"  [{M[0,0]:+.4f}  {M[0,1]:+.4f}]<br>")
            lines.append(f"  [{M[1,0]:+.4f}  {M[1,1]:+.4f}]<br>")
        lines.append("<br>Parameters:<br>")
        for k, v in element.params.items():
            lines.append(f"  {k} = {v:.6g}<br>")
        return "".join(lines)


class DropZone(QFrame):
    """Vertical drop indicator between blocks."""

    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self.index = index
        self.setFixedWidth(6)
        self.setFixedHeight(BLOCK_H)
        self.setVisible(False)
        self.setStyleSheet(f"background:{theme.ACCENT}; border-radius:3px;")


class LatticeLine(QWidget):
    element_selected       = Signal(str)       # uid — single click
    element_double_clicked = Signal(str)       # uid — double click
    element_removed        = Signal(str)       # uid
    order_changed          = Signal(list)      # list of uids

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFixedHeight(90)

        self._outer_layout = QHBoxLayout(self)
        self._outer_layout.setContentsMargins(4, 4, 4, 4)
        self._outer_layout.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setWidgetResizable(False)
        self._scroll.setStyleSheet(f"QScrollArea {{ background:{theme.MANTLE}; border:1px solid {theme.BORDER}; border-radius:6px; }}")
        self._outer_layout.addWidget(self._scroll)

        self._strip = QWidget()
        self._strip.setFixedHeight(BLOCK_H + 8)
        self._strip_layout = QHBoxLayout(self._strip)
        self._strip_layout.setContentsMargins(8, 4, 8, 4)
        self._strip_layout.setSpacing(6)
        self._strip_layout.addStretch()
        self._scroll.setWidget(self._strip)

        self._blocks: list[ElementBlock] = []
        self._elements: list[Element] = []
        self._selected_uid: str | None = None

        self._empty_label = QLabel("← Click elements in the palette to build your lattice")
        self._empty_label.setStyleSheet(f"color:{theme.FG_LBL}; font-size:{theme.FONT_SMALL}px;")
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._strip_layout.insertWidget(0, self._empty_label)

    def set_elements(self, elements: list[Element]):
        self._elements = list(elements)
        self._rebuild()

    def _rebuild(self):
        # Remove old blocks
        for blk in self._blocks:
            blk.hide()
            self._strip_layout.removeWidget(blk)
            blk.deleteLater()
        self._blocks.clear()

        self._empty_label.setVisible(len(self._elements) == 0)

        for elem in self._elements:
            blk = ElementBlock(elem)
            blk.selected.connect(self._on_block_selected)
            blk.double_clicked.connect(self.element_double_clicked)
            blk.removed.connect(self._on_block_removed)
            blk.set_selected(elem.uid == self._selected_uid)
            self._strip_layout.insertWidget(self._strip_layout.count() - 1, blk)
            self._blocks.append(blk)

        # Resize strip
        total_w = len(self._elements) * (BLOCK_W + 6) + 24
        self._strip.setFixedWidth(max(total_w, 400))

    def _on_block_selected(self, uid: str):
        self._selected_uid = uid
        for blk in self._blocks:
            blk.set_selected(blk._uid == uid)
        self.element_selected.emit(uid)

    def _on_block_removed(self, uid: str):
        if self._selected_uid == uid:
            self._selected_uid = None
        self.element_removed.emit(uid)

    # ── Drag and drop reorder ────────────────────────────────────

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        uid = event.mimeData().text()
        drop_x = event.position().x() + self._scroll.horizontalScrollBar().value() - 8
        new_index = max(0, min(int(drop_x / (BLOCK_W + 6)), len(self._elements) - 1))

        # Reorder
        old_index = next((i for i, e in enumerate(self._elements) if e.uid == uid), None)
        if old_index is not None and old_index != new_index:
            elem = self._elements.pop(old_index)
            self._elements.insert(new_index, elem)
            self.order_changed.emit([e.uid for e in self._elements])
        else:
            self._rebuild()
        event.acceptProposedAction()
