"""
gui/element_editor.py
---------------------
Floating dialog that appears when a user clicks an element block.
Shows: element type, label edit, thin/thick toggle, all parameters,
annotation field, and a "What-if" sweep slider.
"""

from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QDoubleSpinBox, QCheckBox, QPushButton, QFrame, QGroupBox,
    QFormLayout, QTextEdit, QSlider, QComboBox, QWidget
)
import numpy as np
import theme
from models.element import Element, ELEMENT_META, ParamSpec


class ParamRow(QWidget):
    """One parameter: label + spinbox + unit."""
    value_changed = Signal(str, float)   # param_name, new_value

    def __init__(self, spec: ParamSpec, current_val: float, parent=None):
        super().__init__(parent)
        self._name = spec.name
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        lbl = QLabel(f"{spec.label}")
        lbl.setFixedWidth(80)
        lbl.setStyleSheet(f"color:{theme.FG_LBL}; font-size:{theme.FONT_SMALL}px;")
        layout.addWidget(lbl)

        self._spin = QDoubleSpinBox()
        self._spin.setDecimals(6)
        self._spin.setRange(spec.min_val, spec.max_val)
        self._spin.setValue(current_val)
        self._spin.setSingleStep(abs(current_val) * 0.05 if current_val != 0 else 0.1)
        self._spin.setStyleSheet(f"""
            QDoubleSpinBox {{
                background: {theme.MANTLE};
                color: {theme.FG};
                border: 1px solid {theme.BORDER};
                border-radius: 3px;
                padding: 2px 4px;
                font-size: {theme.FONT_SMALL}px;
            }}
            QDoubleSpinBox:focus {{ border-color: {theme.ACCENT}; }}
        """)
        self._spin.valueChanged.connect(
            lambda v: self.value_changed.emit(self._name, v)
        )
        layout.addWidget(self._spin, 1)

        if spec.unit:
            unit_lbl = QLabel(spec.unit)
            unit_lbl.setFixedWidth(36)
            unit_lbl.setStyleSheet(f"color:{theme.FG_LBL}; font-size:{theme.FONT_TINY}px;")
            layout.addWidget(unit_lbl)

        if spec.tooltip:
            self.setToolTip(spec.tooltip)

    def set_value(self, v: float):
        self._spin.blockSignals(True)
        self._spin.setValue(v)
        self._spin.blockSignals(False)


class ElementEditor(QDialog):
    params_changed = Signal(str, dict)   # uid, {param: value}
    element_closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setWindowTitle("Element Editor")
        self.setFixedWidth(300)
        self.setStyleSheet(theme.qss_base())

        self._uid: str | None = None
        self._elem: Element | None = None
        self._param_rows: dict[str, ParamRow] = {}
        self._pending: dict[str, float] = {}

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Header: element type
        self._type_label = QLabel("—")
        self._type_label.setStyleSheet(
            f"color:{theme.ACCENT}; font-size:{theme.FONT_HEADER}px; font-weight:bold;")
        layout.addWidget(self._type_label)

        # Label edit
        lbl_row = QHBoxLayout()
        lbl_lbl = QLabel("Label:")
        lbl_lbl.setStyleSheet(f"color:{theme.FG_LBL}; font-size:{theme.FONT_SMALL}px;")
        lbl_lbl.setFixedWidth(50)
        self._label_edit = QLineEdit()
        self._label_edit.setStyleSheet(f"""
            QLineEdit {{
                background: {theme.MANTLE}; color: {theme.FG};
                border: 1px solid {theme.BORDER}; border-radius: 3px;
                padding: 3px 6px; font-size: {theme.FONT_SMALL}px;
            }}
            QLineEdit:focus {{ border-color: {theme.ACCENT}; }}
        """)
        self._label_edit.editingFinished.connect(self._on_label_changed)
        lbl_row.addWidget(lbl_lbl)
        lbl_row.addWidget(self._label_edit)
        layout.addLayout(lbl_row)

        # Thin/thick toggle
        self._thin_cb = QCheckBox("Thin lens approximation")
        self._thin_cb.setStyleSheet(f"color:{theme.FG_DIM}; font-size:{theme.FONT_SMALL}px;")
        self._thin_cb.toggled.connect(self._on_thin_toggled)
        layout.addWidget(self._thin_cb)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color:{theme.BORDER};")
        layout.addWidget(sep)

        # Parameters area
        self._params_group = QGroupBox("Parameters")
        self._params_group.setStyleSheet(f"""
            QGroupBox {{ background:{theme.PANEL}; border:1px solid {theme.BORDER};
                         border-radius:5px; margin-top:8px; }}
            QGroupBox::title {{ color:{theme.CRUST}; background:{theme.ACCENT};
                                padding:2px 8px; border-radius:3px;
                                subcontrol-origin:margin; left:8px; }}
        """)
        self._params_layout = QVBoxLayout(self._params_group)
        self._params_layout.setSpacing(4)
        layout.addWidget(self._params_group)

        # Annotation
        ann_lbl = QLabel("Note:")
        ann_lbl.setStyleSheet(f"color:{theme.FG_LBL}; font-size:{theme.FONT_SMALL}px;")
        layout.addWidget(ann_lbl)
        self._annotation = QTextEdit()
        self._annotation.setFixedHeight(52)
        self._annotation.setStyleSheet(f"""
            QTextEdit {{
                background: {theme.MANTLE}; color: {theme.FG};
                border: 1px solid {theme.BORDER}; border-radius: 3px;
                font-size: {theme.FONT_SMALL}px;
            }}
        """)
        self._annotation.textChanged.connect(self._on_annotation_changed)
        layout.addWidget(self._annotation)

        # Matrix preview (live)
        sep2 = QFrame(); sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet(f"color:{theme.BORDER};")
        layout.addWidget(sep2)

        mat_lbl = QLabel("Transfer matrix (2×2):")
        mat_lbl.setStyleSheet(f"color:{theme.FG_LBL}; font-size:{theme.FONT_SMALL}px;")
        layout.addWidget(mat_lbl)

        self._matrix_preview = QLabel("—")
        self._matrix_preview.setStyleSheet(
            f"font-family:monospace; color:{theme.FG}; font-size:{theme.FONT_SMALL}px;"
            f"background:{theme.MANTLE}; padding:4px; border-radius:3px;")
        self._matrix_preview.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        layout.addWidget(self._matrix_preview)

        # ── What-if sweep ────────────────────────────────────────────
        sep3 = QFrame(); sep3.setFrameShape(QFrame.HLine)
        sep3.setStyleSheet(f"color:{theme.BORDER};")
        layout.addWidget(sep3)

        sweep_hdr = QLabel("What-if sweep")
        sweep_hdr.setStyleSheet(
            f"color:{theme.ACCENT}; font-size:{theme.FONT_SMALL}px; "
            f"font-weight:bold;")
        layout.addWidget(sweep_hdr)

        # Parameter selector
        sweep_row1 = QHBoxLayout()
        sweep_row1.setSpacing(6)
        sp_lbl = QLabel("Param:")
        sp_lbl.setStyleSheet(
            f"color:{theme.FG_LBL}; font-size:{theme.FONT_SMALL}px;")
        sp_lbl.setFixedWidth(48)
        self._sweep_combo = QComboBox()
        self._sweep_combo.setStyleSheet(f"""
            QComboBox {{background:{theme.MANTLE}; color:{theme.FG};
                border:1px solid {theme.BORDER}; border-radius:3px;
                padding:2px 4px; font-size:{theme.FONT_SMALL}px;}}
            QComboBox QAbstractItemView {{
                background:{theme.PANEL}; color:{theme.FG};
                selection-background-color:{theme.ACCENT};
                selection-color:{theme.CRUST};}}
        """)
        sweep_row1.addWidget(sp_lbl)
        sweep_row1.addWidget(self._sweep_combo, 1)
        layout.addLayout(sweep_row1)

        # Range row
        sweep_row2 = QHBoxLayout()
        sweep_row2.setSpacing(4)
        for lbl_txt, attr in [("Min:", "_sweep_min"), ("Max:", "_sweep_max")]:
            lbl = QLabel(lbl_txt)
            lbl.setStyleSheet(
                f"color:{theme.FG_LBL}; font-size:{theme.FONT_TINY}px;")
            lbl.setFixedWidth(28)
            spin = QDoubleSpinBox()
            spin.setDecimals(4)
            spin.setRange(-1e6, 1e6)
            spin.setFixedWidth(80)
            spin.setStyleSheet(f"""
                QDoubleSpinBox {{background:{theme.MANTLE}; color:{theme.FG};
                    border:1px solid {theme.BORDER}; border-radius:3px;
                    padding:2px 4px; font-size:{theme.FONT_TINY}px;}}
                QDoubleSpinBox:focus {{border-color:{theme.ACCENT};}}
            """)
            sweep_row2.addWidget(lbl)
            sweep_row2.addWidget(spin)
            setattr(self, attr, spin)
        layout.addLayout(sweep_row2)

        # Sweep slider
        self._sweep_slider = QSlider(Qt.Horizontal)
        self._sweep_slider.setRange(0, 100)
        self._sweep_slider.setValue(50)
        self._sweep_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background:{theme.MANTLE}; height:5px; border-radius:2px;}}
            QSlider::handle:horizontal {{
                background:{theme.ACCENT}; width:14px; height:14px;
                margin:-5px 0; border-radius:7px;}}
            QSlider::sub-page:horizontal {{
                background:{theme.ACCENT}; border-radius:2px;}}
        """)
        self._sweep_val_lbl = QLabel("—")
        self._sweep_val_lbl.setStyleSheet(
            f"color:{theme.FG}; font-size:{theme.FONT_TINY}px; "
            f"font-family:monospace; min-width:60px;")
        sweep_row3 = QHBoxLayout()
        sweep_row3.addWidget(self._sweep_slider, 1)
        sweep_row3.addWidget(self._sweep_val_lbl)
        layout.addLayout(sweep_row3)

        self._sweep_slider.valueChanged.connect(self._on_sweep_changed)
        self._sweep_combo.currentTextChanged.connect(self._on_sweep_param_changed)
        self._sweep_min.valueChanged.connect(self._on_sweep_range_changed)
        self._sweep_max.valueChanged.connect(self._on_sweep_range_changed)

        # Buttons
        btn_row = QHBoxLayout()
        self._btn_close = QPushButton("Close")
        self._btn_close.clicked.connect(self._on_close)
        btn_row.addStretch()
        btn_row.addWidget(self._btn_close)
        layout.addLayout(btn_row)

    # ── Public API ───────────────────────────────────────────────

    def set_element(self, element: Element):
        self._elem = element
        self._uid  = element.uid

        self._type_label.setText(element.etype.value)
        self._label_edit.setText(element.label)

        thin_supported = element.supports_thin
        self._thin_cb.setVisible(thin_supported)
        self._thin_cb.blockSignals(True)
        self._thin_cb.setChecked(element.thin)
        self._thin_cb.blockSignals(False)

        # Rebuild parameter rows
        for row in self._param_rows.values():
            row.deleteLater()
        self._param_rows.clear()

        for spec in element.param_specs:
            row = ParamRow(spec, element.params.get(spec.name, spec.default))
            row.value_changed.connect(self._on_param_changed)
            self._params_layout.addWidget(row)
            self._param_rows[spec.name] = row

        self._annotation.blockSignals(True)
        self._annotation.setPlainText(element.annotation)
        self._annotation.blockSignals(False)

        self._update_matrix_preview()
        self._populate_sweep_combo()
        self.adjustSize()

    # ── Internal handlers ────────────────────────────────────────

    def _on_label_changed(self):
        if self._elem:
            self._elem.label = self._label_edit.text()
            self.params_changed.emit(self._uid, {})

    def _on_thin_toggled(self, checked: bool):
        if self._elem:
            self._elem.thin = checked
            self._update_matrix_preview()
            self.params_changed.emit(self._uid, dict(self._elem.params))

    def _on_param_changed(self, name: str, value: float):
        if self._elem:
            self._elem.params[name] = value
            self._update_matrix_preview()
            self.params_changed.emit(self._uid, dict(self._elem.params))

    def _on_annotation_changed(self):
        if self._elem:
            self._elem.annotation = self._annotation.toPlainText()

    def _on_close(self):
        self.element_closed.emit()
        self.hide()

    def _update_matrix_preview(self):
        if self._elem is None:
            self._matrix_preview.setText("—")
            return
        try:
            M = self._elem.matrix6()
            # Show the x,x' and y,y' 2×2 blocks for compactness
            lines = [
                "x-plane:",
                f"[ {M[0,0]:+.4f}  {M[0,1]:+.4f} ]",
                f"[ {M[1,0]:+.4f}  {M[1,1]:+.4f} ]",
                "y-plane:",
                f"[ {M[2,2]:+.4f}  {M[2,3]:+.4f} ]",
                f"[ {M[3,2]:+.4f}  {M[3,3]:+.4f} ]",
                f"R₁₆={M[0,5]:+.4f}  R₅₆={M[4,5]:+.4f}",
            ]
            self._matrix_preview.setText("\n".join(lines))
        except Exception as e:
            self._matrix_preview.setText(f"Error: {e}")

    # ── Sweep methods ────────────────────────────────────────────

    def _populate_sweep_combo(self):
        """Fill sweep parameter combo with this element's param names."""
        self._sweep_combo.blockSignals(True)
        self._sweep_combo.clear()
        if self._elem:
            for spec in self._elem.param_specs:
                self._sweep_combo.addItem(spec.name)
        self._sweep_combo.blockSignals(False)
        self._on_sweep_param_changed(self._sweep_combo.currentText())

    def _on_sweep_param_changed(self, name: str):
        """Param selection changed — set default min/max from spec."""
        if not self._elem or not name:
            return
        spec = next((s for s in self._elem.param_specs if s.name == name), None)
        if spec is None:
            return
        cur = self._elem.params.get(name, spec.default)
        # Default range: ±50% of current value (or ±1 if zero)
        half = abs(cur) * 0.5 if abs(cur) > 1e-10 else 1.0
        self._sweep_min.blockSignals(True)
        self._sweep_max.blockSignals(True)
        self._sweep_min.setValue(cur - half)
        self._sweep_max.setValue(cur + half)
        self._sweep_min.blockSignals(False)
        self._sweep_max.blockSignals(False)
        # Reset slider to midpoint (= current value)
        self._sweep_slider.blockSignals(True)
        self._sweep_slider.setValue(50)
        self._sweep_slider.blockSignals(False)
        self._sweep_val_lbl.setText(f"{cur:.5g}")

    def _on_sweep_range_changed(self):
        """Min/max changed — recalculate slider position for current value."""
        if not self._elem:
            return
        name = self._sweep_combo.currentText()
        if not name:
            return
        cur  = self._elem.params.get(name, 0.0)
        vmin = self._sweep_min.value()
        vmax = self._sweep_max.value()
        if abs(vmax - vmin) < 1e-12:
            return
        frac = (cur - vmin) / (vmax - vmin)
        self._sweep_slider.blockSignals(True)
        self._sweep_slider.setValue(int(np.clip(frac * 100, 0, 100)))
        self._sweep_slider.blockSignals(False)

    def _on_sweep_changed(self, slider_val: int):
        """Slider moved — compute new param value and emit update."""
        if not self._elem:
            return
        name = self._sweep_combo.currentText()
        if not name:
            return
        vmin = self._sweep_min.value()
        vmax = self._sweep_max.value()
        frac = slider_val / 100.0
        new_val = vmin + frac * (vmax - vmin)
        self._elem.params[name] = new_val
        self._sweep_val_lbl.setText(f"{new_val:.5g}")
        # Update the spinbox in the param row without triggering its own signal
        if name in self._param_rows:
            self._param_rows[name].set_value(new_val)
        self._update_matrix_preview()
        self.params_changed.emit(self._uid, dict(self._elem.params))

    def closeEvent(self, event):
        self.element_closed.emit()
        event.accept()
