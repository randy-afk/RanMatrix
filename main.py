#!/usr/bin/env python3
"""
RanMatrix  v1.0.0
====================
Interactive 6×6 transfer matrix explorer for accelerator beam optics.
Educational tool covering linear and second-order beam dynamics.

Features:
  - 6×6 R matrix (ELEGANT / MAD-X / Bmad conventions)
  - Second-order T tensor (geometric + chromatic + longitudinal)
  - Twiss propagation — both planes (βx, βy, αx, αy, Dx, Dy)
  - Phase space ellipses with interactive ghost selection
  - Twiss function plot βx(s), βy(s)
  - Step mode animation — element-by-element matrix and ellipse evolution
  - Parameter sweep — live update as any element parameter varies
  - Preset lattices: FODO, chicane, dogleg, triplet, simple ring
  - Export: ELEGANT, Bmad, numpy, session JSON

Author:  Randika Gamage  (randika@jlab.org)
Support: Absolutely not. Figure it out.

Usage:
    python main.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon, QPixmap

import theme

__version__ = "1.0.0"
__author__  = "Randika Gamage"
__email__   = "randika@jlab.org"


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("RanMatrix")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("Jefferson Lab")

    # App icon
    icon_path = Path(__file__).parent / "assets" / "logo_gui.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Apply global stylesheet and matplotlib theme
    theme.apply_mpl_theme()
    app.setStyleSheet(theme.qss_base())

    font = QFont("Segoe UI", theme.FONT_BODY)
    app.setFont(font)

    from gui.main_window import MainWindow
    win = MainWindow()
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
