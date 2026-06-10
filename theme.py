# ---------------------------------------------------------------
# RanMatrix — theme.py
# RanOptics color palette (standalone copy)
# Dark teal/green base with warm orange accent.
# ---------------------------------------------------------------

# ── Background layers (darkest → lightest) ──────────────────────
CRUST    = "#192E26"   # menubar, header, statusbar
MANTLE   = "#1E3A30"   # input field backgrounds
PANEL    = "#234438"   # panel / sidebar backgrounds
BG       = "#2C5446"   # main window background
SURFACE2 = "#3A6858"   # hover states, raised surfaces
BORDER   = "#5A8A78"   # all borders — use this and nothing else

# ── Text hierarchy ───────────────────────────────────────────────
FG       = "#EEF5F2"   # primary text — values, content
FG_DIM   = "#A8C4BC"   # secondary text, descriptions
FG_LBL   = "#8AB0A6"   # labels, captions, axis names

# ── Accent ───────────────────────────────────────────────────────
ACCENT   = "#FDA769"   # buttons, active tabs, highlights
ACCENT2  = "#FD8C3A"   # pressed / hover on accent elements
# Rule: text ON orange backgrounds always uses CRUST, never FG

# ── Semantic ─────────────────────────────────────────────────────
SUCCESS  = "#69db7c"   # ok, stable, valid
WARN     = "#ffd60a"   # warning, caution
ERROR    = "#ff453a"   # error, unstable, conflict

# ── Physics / plot colors ────────────────────────────────────────
# Fixed conventions — keep consistent across all panels
TWISS_A    = "#74c0fc"   # βx, αx — always blue
TWISS_B    = "#69db7c"   # βy, αy — always green (== SUCCESS)
COLOR_DISP = "#FDA769"   # Dx — orange (== ACCENT)
COLOR_PHASE_ELLIPSE = "#74c0fc"   # phase space ellipse — blue
COLOR_PARTICLE      = "#FDA769"   # single particle overlay — orange
COLOR_GHOST         = "#5A8A78"   # ghost ellipses at boundaries

# ── Element block colors (palette) ──────────────────────────────
# Each element type gets a distinct block color in the lattice line
ELEM_DRIFT      = "#4A7A6A"   # muted teal
ELEM_QUAD_F     = "#5B9BD5"   # soft blue  (focusing)
ELEM_QUAD_D     = "#C0504D"   # soft red   (defocusing)
ELEM_DIPOLE     = "#8E6BBF"   # purple
ELEM_SEXTUPOLE  = "#E07B39"   # amber-orange
ELEM_OCTUPOLE   = "#C0963C"   # gold
ELEM_RF         = "#4BACC6"   # cyan-teal
ELEM_KICKER     = "#70AD47"   # green
ELEM_APERTURE   = "#808080"   # grey
ELEM_MULTIPOLE  = "#D4869C"   # rose
ELEM_MARKER     = "#A8C4BC"   # FG_DIM (subtle)
ELEM_MISALIGN   = "#FDA769"   # orange (wrapper)

# ── Font sizes ───────────────────────────────────────────────────
# Base sizes — scaled by FONT_SCALE at runtime.
# Call set_font_scale(factor) to change globally, then reapply QSS.
_FONT_SCALE: float = 1.0

_BASE_TINY   = 9
_BASE_SMALL  = 11
_BASE_BODY   = 13
_BASE_LABEL  = 12
_BASE_HEADER = 15
_BASE_TITLE  = 18

def set_font_scale(scale: float):
    """Set global font scale (0.7–1.5 range). Updates all FONT_* globals."""
    global _FONT_SCALE, FONT_TINY, FONT_SMALL, FONT_BODY, FONT_LABEL, FONT_HEADER, FONT_TITLE
    _FONT_SCALE  = max(0.5, min(2.0, scale))
    FONT_TINY    = max(7,  round(_BASE_TINY   * _FONT_SCALE))
    FONT_SMALL   = max(8,  round(_BASE_SMALL  * _FONT_SCALE))
    FONT_BODY    = max(9,  round(_BASE_BODY   * _FONT_SCALE))
    FONT_LABEL   = max(8,  round(_BASE_LABEL  * _FONT_SCALE))
    FONT_HEADER  = max(10, round(_BASE_HEADER * _FONT_SCALE))
    FONT_TITLE   = max(12, round(_BASE_TITLE  * _FONT_SCALE))

def get_font_scale() -> float:
    return _FONT_SCALE

# Initialise at default scale
FONT_TINY   = _BASE_TINY
FONT_SMALL  = _BASE_SMALL
FONT_BODY   = _BASE_BODY
FONT_LABEL  = _BASE_LABEL
FONT_HEADER = _BASE_HEADER
FONT_TITLE  = _BASE_TITLE

# ── Matplotlib rc params — call apply_mpl_theme() once at startup ─
import matplotlib as mpl

def apply_mpl_theme():
    """Apply RanOptics dark theme to all matplotlib figures."""
    mpl.rcParams.update({
        "figure.facecolor":  BG,
        "axes.facecolor":    PANEL,
        "axes.edgecolor":    BORDER,
        "axes.labelcolor":   FG_LBL,
        "axes.titlecolor":   FG,
        "xtick.color":       FG_LBL,
        "ytick.color":       FG_LBL,
        "text.color":        FG,
        "grid.color":        BORDER,
        "grid.alpha":        0.4,
        "grid.linestyle":    "--",
        "legend.facecolor":  PANEL,
        "legend.edgecolor":  BORDER,
        "legend.labelcolor": FG,
        "lines.linewidth":   1.8,
        "font.size":         FONT_SMALL,
        "axes.titlesize":    FONT_BODY,
        "axes.labelsize":    FONT_LABEL,
    })


def qss_base() -> str:
    """
    Return the base Qt stylesheet for all widgets.
    Apply once via QApplication.setStyleSheet(qss_base()).
    """
    return f"""
    /* ── Global ────────────────────────────────────────────── */
    QWidget {{
        background-color: {BG};
        color: {FG};
        font-size: {FONT_BODY}px;
        font-family: "Inter", "Segoe UI", "Helvetica Neue", sans-serif;
    }}
    QMainWindow {{
        background-color: {CRUST};
    }}

    /* ── Panels / frames ────────────────────────────────────── */
    QFrame {{
        background-color: transparent;
        border: none;
    }}
    QGroupBox {{
        background-color: {PANEL};
        border: 1px solid {BORDER};
        border-radius: 6px;
        margin-top: 20px;
        padding-top: 6px;
    }}
    QGroupBox::title {{
        color: {CRUST};
        background-color: {ACCENT};
        padding: 2px 10px;
        border-radius: 4px;
        font-size: {FONT_SMALL}px;
        font-weight: bold;
        letter-spacing: 1px;
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 10px;
        top: -2px;
    }}

    /* ── Buttons ────────────────────────────────────────────── */
    QPushButton {{
        background-color: {SURFACE2};
        color: {FG};
        border: 1px solid {BORDER};
        border-radius: 5px;
        padding: 4px 10px;
        font-size: {FONT_SMALL}px;
    }}
    QPushButton:hover {{
        background-color: {ACCENT};
        color: {CRUST};
        border-color: {ACCENT};
    }}
    QPushButton:pressed {{
        background-color: {ACCENT2};
        color: {CRUST};
    }}
    QPushButton:disabled {{
        background-color: {MANTLE};
        color: {FG_LBL};
        border-color: {MANTLE};
    }}

    /* ── Accent / primary buttons ───────────────────────────── */
    QPushButton[accent="true"] {{
        background-color: {ACCENT};
        color: {CRUST};
        border-color: {ACCENT};
        font-weight: bold;
    }}
    QPushButton[accent="true"]:hover {{
        background-color: {ACCENT2};
    }}

    /* ── Inputs ─────────────────────────────────────────────── */
    QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox {{
        background-color: {MANTLE};
        color: {FG};
        border: 1px solid {BORDER};
        border-radius: 4px;
        padding: 3px 6px;
        font-size: {FONT_BODY}px;
    }}
    QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus {{
        border-color: {ACCENT};
    }}
    QComboBox::drop-down {{
        border: none;
    }}
    QComboBox QAbstractItemView {{
        background-color: {PANEL};
        color: {FG};
        selection-background-color: {ACCENT};
        selection-color: {CRUST};
        border: 1px solid {BORDER};
    }}

    /* ── Sliders ────────────────────────────────────────────── */
    QSlider::groove:horizontal {{
        background: {MANTLE};
        height: 4px;
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        background: {ACCENT};
        width: 14px;
        height: 14px;
        margin: -5px 0;
        border-radius: 7px;
    }}
    QSlider::sub-page:horizontal {{
        background: {ACCENT};
        border-radius: 2px;
    }}

    /* ── Tab widget ─────────────────────────────────────────── */
    QTabWidget::pane {{
        background-color: {PANEL};
        border: 1px solid {BORDER};
        border-radius: 4px;
    }}
    QTabBar::tab {{
        background-color: {MANTLE};
        color: {FG_DIM};
        border: 1px solid {BORDER};
        border-bottom: none;
        padding: 5px 14px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        font-size: {FONT_SMALL}px;
    }}
    QTabBar::tab:selected {{
        background-color: {ACCENT};
        color: {CRUST};
        font-weight: bold;
    }}
    QTabBar::tab:hover:!selected {{
        background-color: {SURFACE2};
        color: {FG};
    }}

    /* ── Scrollbars ─────────────────────────────────────────── */
    QScrollBar:vertical {{
        background: {MANTLE};
        width: 8px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: {BORDER};
        min-height: 20px;
        border-radius: 4px;
    }}
    QScrollBar:horizontal {{
        background: {MANTLE};
        height: 8px;
        border-radius: 4px;
    }}
    QScrollBar::handle:horizontal {{
        background: {BORDER};
        min-width: 20px;
        border-radius: 4px;
    }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}

    /* ── Tooltips ───────────────────────────────────────────── */
    QToolTip {{
        background-color: {CRUST};
        color: {FG};
        border: 1px solid {BORDER};
        padding: 4px 8px;
        border-radius: 4px;
        font-size: {FONT_SMALL}px;
    }}

    /* ── Splitter ───────────────────────────────────────────── */
    QSplitter::handle {{
        background-color: {BORDER};
    }}
    QSplitter::handle:horizontal {{ width: 2px; }}
    QSplitter::handle:vertical   {{ height: 2px; }}

    /* ── Labels ─────────────────────────────────────────────── */
    QLabel[role="header"] {{
        color: {ACCENT};
        font-size: {FONT_HEADER}px;
        font-weight: bold;
    }}
    QLabel[role="label"] {{
        color: {FG_LBL};
        font-size: {FONT_LABEL}px;
    }}
    QLabel[role="value"] {{
        color: {FG};
        font-size: {FONT_BODY}px;
        font-weight: bold;
    }}
    QLabel[role="dim"] {{
        color: {FG_DIM};
        font-size: {FONT_SMALL}px;
    }}

    /* ── CheckBox / RadioButton ─────────────────────────────── */
    QCheckBox, QRadioButton {{
        color: {FG};
        spacing: 6px;
    }}
    QCheckBox::indicator, QRadioButton::indicator {{
        width: 14px;
        height: 14px;
        border: 1px solid {BORDER};
        border-radius: 3px;
        background: {MANTLE};
    }}
    QCheckBox::indicator:checked {{
        background-color: {ACCENT};
        border-color: {ACCENT};
    }}

    /* ── Status bar ─────────────────────────────────────────── */
    QStatusBar {{
        background-color: {CRUST};
        color: {FG_DIM};
        font-size: {FONT_SMALL}px;
        border-top: 1px solid {BORDER};
    }}

    /* ── Menu bar ───────────────────────────────────────────── */
    QMenuBar {{
        background-color: {CRUST};
        color: {FG};
        border-bottom: 1px solid {BORDER};
    }}
    QMenuBar::item:selected {{
        background-color: {SURFACE2};
    }}
    QMenu {{
        background-color: {PANEL};
        color: {FG};
        border: 1px solid {BORDER};
    }}
    QMenu::item:selected {{
        background-color: {ACCENT};
        color: {CRUST};
    }}
    """
