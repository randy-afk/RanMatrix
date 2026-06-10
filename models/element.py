"""
models/element.py
-----------------
Element definitions, type enum, parameter schemas, 6×6 matrix dispatch.
"""

from __future__ import annotations
import uuid
from enum import Enum
from dataclasses import dataclass, field
from typing import Any
import numpy as np

from physics import matrices as mx
from theme import (
    ELEM_DRIFT, ELEM_QUAD_F, ELEM_QUAD_D, ELEM_DIPOLE,
    ELEM_SEXTUPOLE, ELEM_OCTUPOLE, ELEM_RF, ELEM_KICKER,
    ELEM_APERTURE, ELEM_MULTIPOLE, ELEM_MARKER, ELEM_MISALIGN
)

# Solenoid colour — add to theme fallback
ELEM_SOLENOID = "#2E86AB"


class ElementType(Enum):
    DRIFT          = "Drift"
    QUAD_F         = "Quad F"
    QUAD_D         = "Quad D"
    DIPOLE_SECTOR  = "Dipole (sector)"
    DIPOLE_RECT    = "Dipole (rect)"
    SOLENOID       = "Solenoid"
    SEXTUPOLE      = "Sextupole"
    OCTUPOLE       = "Octupole"
    RF_CAVITY      = "RF Cavity"
    H_KICKER       = "H Kicker"
    V_KICKER       = "V Kicker"
    APERTURE_CIRC  = "Aperture (circ)"
    APERTURE_RECT  = "Aperture (rect)"
    THIN_MULTIPOLE = "Thin Multipole"
    MISALIGN       = "Misaligned"
    MARKER         = "Marker"


@dataclass
class ParamSpec:
    name:    str
    label:   str
    default: float
    min_val: float = -1e9
    max_val: float =  1e9
    unit:    str   = ""
    tooltip: str   = ""


ELEMENT_META: dict[ElementType, dict] = {
    ElementType.DRIFT: {
        "label": "Drift", "color": ELEM_DRIFT, "abbrev": "D",
        "supports_thin": False,
        "params": [ParamSpec("L", "Length", 1.0, 0.0, 1000.0, "m", "Drift length")],
    },
    ElementType.QUAD_F: {
        "label": "Quad F", "color": ELEM_QUAD_F, "abbrev": "QF",
        "supports_thin": True,
        "params": [
            ParamSpec("L",  "Length",    0.5,    0.0,  100.0,  "m",   "Quad length"),
            ParamSpec("K1", "K1 (grad)", 1.0,  -100.0, 100.0,  "m⁻²", "Norm. quad gradient (K1>0 → x-focusing)"),
        ],
    },
    ElementType.QUAD_D: {
        "label": "Quad D", "color": ELEM_QUAD_D, "abbrev": "QD",
        "supports_thin": True,
        "params": [
            ParamSpec("L",  "Length",    0.5,    0.0,  100.0,  "m",   "Quad length"),
            ParamSpec("K1", "K1 (grad)", 1.0,  -100.0, 100.0,  "m⁻²", "Stored as +, applied as −K1"),
        ],
    },
    ElementType.DIPOLE_SECTOR: {
        "label": "Dipole (sector)", "color": ELEM_DIPOLE, "abbrev": "B",
        "supports_thin": True,
        "params": [
            ParamSpec("L",     "Length",     1.0,  0.0,    100.0,       "m",   "Arc length"),
            ParamSpec("theta", "Bend angle", 0.1, -np.pi,  np.pi,       "rad", "Total bend angle"),
            ParamSpec("e1",    "e1 (entry)", 0.0, -np.pi/2, np.pi/2,   "rad", "Entrance pole-face angle"),
            ParamSpec("e2",    "e2 (exit)",  0.0, -np.pi/2, np.pi/2,   "rad", "Exit pole-face angle"),
        ],
    },
    ElementType.DIPOLE_RECT: {
        "label": "Dipole (rect)", "color": ELEM_DIPOLE, "abbrev": "BR",
        "supports_thin": True,
        "params": [
            ParamSpec("L",     "Length",     1.0,  0.0,   100.0,  "m",   "Path length"),
            ParamSpec("theta", "Bend angle", 0.1, -np.pi,  np.pi, "rad", "Total bend angle"),
        ],
    },
    ElementType.SOLENOID: {
        "label": "Solenoid", "color": ELEM_SOLENOID, "abbrev": "SOL",
        "supports_thin": False,
        "params": [
            ParamSpec("L",  "Length",  1.0, 0.0, 100.0, "m",    "Solenoid length"),
            ParamSpec("Ks", "Ks",      0.5, -50,  50.0, "m⁻¹",  "Integrated solenoid strength Ks=B_s·L/(B·ρ)"),
        ],
    },
    ElementType.SEXTUPOLE: {
        "label": "Sextupole", "color": ELEM_SEXTUPOLE, "abbrev": "SF",
        "supports_thin": True,
        "params": [
            ParamSpec("L",  "Length", 0.2,  0.0, 100.0, "m",   "Length"),
            ParamSpec("K2", "K2",     0.0, -1e6,  1e6,  "m⁻³", "Sextupole strength"),
        ],
    },
    ElementType.OCTUPOLE: {
        "label": "Octupole", "color": ELEM_OCTUPOLE, "abbrev": "OC",
        "supports_thin": True,
        "params": [
            ParamSpec("L",  "Length", 0.1,  0.0, 100.0, "m",   "Length"),
            ParamSpec("K3", "K3",     0.0, -1e8,  1e8,  "m⁻⁴", "Octupole strength"),
        ],
    },
    ElementType.RF_CAVITY: {
        "label": "RF Cavity", "color": ELEM_RF, "abbrev": "RF",
        "supports_thin": True,
        "params": [
            ParamSpec("V",   "Voltage", 1e6,    0.0,   1e9,   "V",   "Peak RF voltage"),
            ParamSpec("phi", "Phase",   0.0,  -np.pi,  np.pi, "rad", "Synchronous phase"),
            ParamSpec("f",   "Freq.",   1.5e9,  0.0,   1e12,  "Hz",  "RF frequency"),
        ],
    },
    ElementType.H_KICKER: {
        "label": "H Kicker", "color": ELEM_KICKER, "abbrev": "KH",
        "supports_thin": True,
        "params": [ParamSpec("theta_x", "θx kick", 0.0, -0.1, 0.1, "rad", "Horizontal kick angle")],
    },
    ElementType.V_KICKER: {
        "label": "V Kicker", "color": ELEM_KICKER, "abbrev": "KV",
        "supports_thin": True,
        "params": [ParamSpec("theta_y", "θy kick", 0.0, -0.1, 0.1, "rad", "Vertical kick angle")],
    },
    ElementType.APERTURE_CIRC: {
        "label": "Aperture (circ)", "color": ELEM_APERTURE, "abbrev": "AC",
        "supports_thin": False,
        "params": [ParamSpec("r", "Radius", 0.02, 1e-4, 10.0, "m", "Circular aperture radius")],
    },
    ElementType.APERTURE_RECT: {
        "label": "Aperture (rect)", "color": ELEM_APERTURE, "abbrev": "AR",
        "supports_thin": False,
        "params": [
            ParamSpec("hx", "Half-width x", 0.02, 1e-4, 10.0, "m", "Horizontal half-aperture"),
            ParamSpec("hy", "Half-width y", 0.02, 1e-4, 10.0, "m", "Vertical half-aperture"),
        ],
    },
    ElementType.THIN_MULTIPOLE: {
        "label": "Thin Multipole", "color": ELEM_MULTIPOLE, "abbrev": "MP",
        "supports_thin": True,
        "params": [
            ParamSpec("K1L", "K1L (quad)", 0.0, -1e4, 1e4, "m⁻¹", "Integrated quad strength"),
            ParamSpec("K2L", "K2L (sext)", 0.0, -1e4, 1e4, "m⁻²", "Integrated sextupole strength"),
            ParamSpec("K3L", "K3L (oct)",  0.0, -1e4, 1e4, "m⁻³", "Integrated octupole strength"),
        ],
    },
    ElementType.MISALIGN: {
        "label": "Misaligned", "color": ELEM_MISALIGN, "abbrev": "MX",
        "supports_thin": False,
        "params": [
            ParamSpec("dx",     "dx",  0.0, -0.01, 0.01, "m",   "Transverse offset x"),
            ParamSpec("dy",     "dy",  0.0, -0.01, 0.01, "m",   "Transverse offset y"),
            ParamSpec("dtheta", "dθ",  0.0, -0.01, 0.01, "rad", "Roll angle"),
        ],
    },
    ElementType.MARKER: {
        "label": "Marker", "color": ELEM_MARKER, "abbrev": "Mk",
        "supports_thin": False,
        "params": [],
    },
}


def default_params(etype: ElementType) -> dict[str, float]:
    return {p.name: p.default for p in ELEMENT_META[etype]["params"]}


@dataclass
class Element:
    etype:      ElementType
    params:     dict[str, float]  = field(default_factory=dict)
    label:      str               = ""
    thin:       bool              = False
    annotation: str               = ""
    uid:        str               = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def __post_init__(self):
        if not self.label:
            self.label = ELEMENT_META[self.etype]["label"]
        for k, v in default_params(self.etype).items():
            if k not in self.params:
                self.params[k] = v

    @property
    def color(self) -> str:
        return ELEMENT_META[self.etype]["color"]

    @property
    def abbrev(self) -> str:
        return ELEMENT_META[self.etype]["abbrev"]

    @property
    def supports_thin(self) -> bool:
        return ELEMENT_META[self.etype]["supports_thin"]

    @property
    def param_specs(self) -> list[ParamSpec]:
        return ELEMENT_META[self.etype]["params"]

    def length(self) -> float:
        if self.thin:
            return 0.0
        return self.params.get("L", 0.0)

    # ── 6×6 matrix ──────────────────────────────────────────────

    def matrix6(self) -> np.ndarray:
        """Return the 6×6 transfer matrix for this element."""
        p  = self.params
        et = self.etype

        if et == ElementType.DRIFT:
            return mx.drift6(p["L"])

        elif et == ElementType.QUAD_F:
            return mx.quad6(p["L"], abs(p["K1"]), thin=self.thin)

        elif et == ElementType.QUAD_D:
            return mx.quad6(p["L"], -abs(p["K1"]), thin=self.thin)

        elif et == ElementType.DIPOLE_SECTOR:
            return mx.dipole_sector6(p["L"], p["theta"],
                                     p["e1"], p["e2"], thin=self.thin)

        elif et == ElementType.DIPOLE_RECT:
            return mx.dipole_rect6(p["L"], p["theta"], thin=self.thin)

        elif et == ElementType.SOLENOID:
            return mx.solenoid6(p["L"], p["Ks"])

        elif et == ElementType.SEXTUPOLE:
            return mx.sextupole6(p["L"], p["K2"], thin=self.thin)

        elif et == ElementType.OCTUPOLE:
            return mx.octupole6(p["L"], p["K3"], thin=self.thin)

        elif et == ElementType.RF_CAVITY:
            return mx.rf_cavity6(p["V"], p["phi"], p["f"])

        elif et == ElementType.H_KICKER:
            return mx.h_kicker6(p["theta_x"])

        elif et == ElementType.V_KICKER:
            return mx.v_kicker6(p["theta_y"])

        elif et in (ElementType.APERTURE_CIRC, ElementType.APERTURE_RECT):
            return mx.I6()

        elif et == ElementType.THIN_MULTIPOLE:
            return mx.thin_multipole6(p.get("K1L", 0.0),
                                      p.get("K2L", 0.0),
                                      p.get("K3L", 0.0))

        elif et == ElementType.MISALIGN:
            return mx.I6()   # orbit offset tracked separately

        else:  # MARKER
            return mx.I6()

    # ── Serialisation ───────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "uid": self.uid, "etype": self.etype.name,
            "label": self.label, "params": dict(self.params),
            "thin": self.thin, "annotation": self.annotation,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Element":
        return cls(
            etype=ElementType[d["etype"]], params=d["params"],
            label=d.get("label", ""), thin=d.get("thin", False),
            annotation=d.get("annotation", ""), uid=d.get("uid", str(uuid.uuid4())[:8]),
        )

    # ── Export ──────────────────────────────────────────────────

    def to_elegant_str(self) -> str:
        p = self.params
        et = self.etype
        name = self.label.upper().replace(" ", "_")
        if et == ElementType.DRIFT:
            return f"{name}: DRIFT, L={p['L']:.6g}"
        elif et == ElementType.QUAD_F:
            return f"{name}: KQUAD, L={p['L']:.6g}, K1={abs(p['K1']):.6g}"
        elif et == ElementType.QUAD_D:
            return f"{name}: KQUAD, L={p['L']:.6g}, K1={-abs(p['K1']):.6g}"
        elif et == ElementType.DIPOLE_SECTOR:
            return (f"{name}: CSBEND, L={p['L']:.6g}, ANGLE={p['theta']:.6g}, "
                    f"E1={p['e1']:.6g}, E2={p['e2']:.6g}")
        elif et == ElementType.DIPOLE_RECT:
            return f"{name}: RBEND, L={p['L']:.6g}, ANGLE={p['theta']:.6g}"
        elif et == ElementType.SOLENOID:
            return f"{name}: SOLE, L={p['L']:.6g}, KS={p['Ks']:.6g}"
        elif et == ElementType.SEXTUPOLE:
            return f"{name}: KSEXT, L={p['L']:.6g}, K2={p['K2']:.6g}"
        elif et == ElementType.MARKER:
            return f"{name}: MARK"
        else:
            return f"! {name}: (no ELEGANT export for {et.value})"

    def to_bmad_str(self) -> str:
        p = self.params
        et = self.etype
        name = self.label.lower().replace(" ", "_")
        if et == ElementType.DRIFT:
            return f"{name}: drift, l={p['L']:.6g}"
        elif et == ElementType.QUAD_F:
            return f"{name}: quadrupole, l={p['L']:.6g}, k1={abs(p['K1']):.6g}"
        elif et == ElementType.QUAD_D:
            return f"{name}: quadrupole, l={p['L']:.6g}, k1={-abs(p['K1']):.6g}"
        elif et == ElementType.DIPOLE_SECTOR:
            rho = p["L"]/p["theta"] if p["theta"] != 0 else 1e9
            return (f"{name}: sbend, l={p['L']:.6g}, g={1/rho:.6g}, "
                    f"e1={p['e1']:.6g}, e2={p['e2']:.6g}")
        elif et == ElementType.DIPOLE_RECT:
            rho = p["L"]/p["theta"] if p["theta"] != 0 else 1e9
            return f"{name}: rbend, l={p['L']:.6g}, g={1/rho:.6g}"
        elif et == ElementType.SOLENOID:
            return f"{name}: solenoid, l={p['L']:.6g}, ks={p['Ks']:.6g}"
        elif et == ElementType.SEXTUPOLE:
            return f"{name}: sextupole, l={p['L']:.6g}, k2={p['K2']:.6g}"
        elif et == ElementType.MARKER:
            return f"{name}: marker"
        else:
            return f"! {name}: (no Bmad export for {et.value})"


def make_element(etype: ElementType, **kwargs) -> Element:
    params = default_params(etype)
    params.update(kwargs)
    return Element(etype=etype, params=params)
