"""
models/lattice.py
-----------------
Lattice — ordered element list, 6×6 compute engine, serialization, export.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Literal, Optional
import numpy as np

from models.element import Element, ElementType, make_element
from physics import matrices as mx
from physics.matrices import (
    product, cumulative_products, is_stable,
    trace_x, trace_y, tune_from_matrix, compute_T_tensor,
    to_bmad, IMPORTANT_T_TERMS, COORD_LABELS, I6
)
from physics.twiss import propagate_twiss_along, ring_periodic_twiss, TwissPoint


@dataclass
class LatticeResult:
    """Everything derived from the current element list. Immutable snapshot."""

    # 6×6 matrices
    R:          np.ndarray              # 6×6 one-turn / end-to-end (internal convention)
    R_each:     list[np.ndarray]        # 6×6 per element
    R_cumul:    list[np.ndarray]        # cumulative 6×6, len=N+1

    # Second-order T tensor
    T:          np.ndarray              # shape (6,6,6)

    # Stability
    trace_x:    float
    trace_y:    float
    stable:     bool
    Qx:         Optional[float]
    Qy:         Optional[float]

    # Twiss along lattice (len=N+1)
    twiss_points: list[TwissPoint]
    s_positions:  list[float]
    n_elements:   int

    # Convenience accessors
    @property
    def betax_list(self)  -> list[float]: return [tp.betax  for tp in self.twiss_points]
    @property
    def betay_list(self)  -> list[float]: return [tp.betay  for tp in self.twiss_points]
    @property
    def alphax_list(self) -> list[float]: return [tp.alphax for tp in self.twiss_points]
    @property
    def alphay_list(self) -> list[float]: return [tp.alphay for tp in self.twiss_points]
    @property
    def phix_list(self)   -> list[float]: return [tp.phix   for tp in self.twiss_points]
    @property
    def phiy_list(self)   -> list[float]: return [tp.phiy   for tp in self.twiss_points]
    @property
    def Dx_list(self)     -> list[float]: return [tp.Dx     for tp in self.twiss_points]
    @property
    def Dxp_list(self)    -> list[float]: return [tp.Dxp    for tp in self.twiss_points]
    @property
    def Dy_list(self)     -> list[float]: return [tp.Dy     for tp in self.twiss_points]
    @property
    def Dyp_list(self)    -> list[float]: return [tp.Dyp    for tp in self.twiss_points]

    def R_in_convention(self, convention: str) -> np.ndarray:
        """Return total R matrix in requested coordinate convention."""
        if convention == "bmad":
            return to_bmad(self.R)
        return self.R   # elegant / madx


class Lattice:
    def __init__(self):
        self.elements:  list[Element] = []
        self.mode:      Literal["linac", "ring"] = "linac"
        self.linear:    bool  = True

        # Initial Twiss (linac mode) — both planes
        self.betax0:  float = 1.0;   self.alphax0: float = 0.0
        self.betay0:  float = 1.0;   self.alphay0: float = 0.0
        self.Dx0:     float = 0.0;   self.Dxp0:   float = 0.0
        self.Dy0:     float = 0.0;   self.Dyp0:   float = 0.0

        # Beam
        self.emittance_x: float = 1e-6
        self.emittance_y: float = 1e-6

        # Single particle initial conditions
        self.x0: float = 1e-3;  self.xp0: float = 0.0
        self.y0: float = 0.0;   self.yp0: float = 0.0
        self.delta_p: float = 0.0

    # ── Element ops ─────────────────────────────────────────────

    def append(self, e: Element):          self.elements.append(e)
    def insert(self, i: int, e: Element):  self.elements.insert(i, e)
    def remove(self, uid: str):            self.elements = [e for e in self.elements if e.uid != uid]
    def move(self, uid: str, i: int):
        e = next((x for x in self.elements if x.uid == uid), None)
        if e: self.elements.remove(e); self.elements.insert(i, e)
    def get(self, uid: str) -> Optional[Element]:
        return next((e for e in self.elements if e.uid == uid), None)
    def clear(self): self.elements.clear()

    def s_positions(self) -> list[float]:
        s = [0.0]
        for e in self.elements: s.append(s[-1] + e.length())
        return s

    def total_length(self) -> float:
        return sum(e.length() for e in self.elements)

    # ── Compute ─────────────────────────────────────────────────

    def compute(self) -> LatticeResult:
        if not self.elements:
            return self._empty_result()

        R_each = [e.matrix6() for e in self.elements]
        R_cumul = cumulative_products(R_each)
        R_total = R_cumul[-1]

        tr_x = trace_x(R_total)
        tr_y = trace_y(R_total)
        stable = is_stable(R_total)
        Qx, Qy = tune_from_matrix(R_total)

        s_pos = self.s_positions()

        # Twiss propagation
        if self.mode == "ring":
            twiss_pts = ring_periodic_twiss(R_total, R_each, s_pos) \
                        or self._flat_twiss(s_pos)
        else:
            twiss_pts = propagate_twiss_along(
                betax0=self.betax0, alphax0=self.alphax0,
                betay0=self.betay0, alphay0=self.alphay0,
                matrices=R_each, s_positions=s_pos,
                Dx0=self.Dx0, Dxp0=self.Dxp0,
                Dy0=self.Dy0, Dyp0=self.Dyp0,
            )

        # T tensor — pass full element list for proper dispatch
        T = compute_T_tensor(R_each, self.elements)

        result = LatticeResult(
            R=R_total, R_each=R_each, R_cumul=R_cumul,
            T=T, trace_x=tr_x, trace_y=tr_y,
            stable=stable, Qx=Qx, Qy=Qy,
            twiss_points=twiss_pts, s_positions=s_pos,
            n_elements=len(self.elements),
        )
        result._elements  = list(self.elements)
        result._elem_uids = [e.uid for e in self.elements]
        return result

    def _empty_result(self) -> LatticeResult:
        tp = TwissPoint(
            s=0.0, betax=self.betax0, alphax=self.alphax0,
            gammax=(1+self.alphax0**2)/self.betax0, phix=0.0,
            betay=self.betay0, alphay=self.alphay0,
            gammay=(1+self.alphay0**2)/self.betay0, phiy=0.0,
        )
        return LatticeResult(
            R=I6(), R_each=[], R_cumul=[I6()],
            T=np.zeros((6,6,6)),
            trace_x=2.0, trace_y=2.0, stable=True, Qx=None, Qy=None,
            twiss_points=[tp], s_positions=[0.0], n_elements=0,
        )

    def _flat_twiss(self, s_pos: list[float]) -> list[TwissPoint]:
        return [TwissPoint(
            s=s, betax=self.betax0, alphax=self.alphax0,
            gammax=(1+self.alphax0**2)/self.betax0, phix=0.0,
            betay=self.betay0, alphay=self.alphay0,
            gammay=(1+self.alphay0**2)/self.betay0, phiy=0.0,
        ) for s in s_pos]

    # ── Serialisation ───────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "version": 2, "mode": self.mode, "linear": self.linear,
            "betax0": self.betax0, "alphax0": self.alphax0,
            "betay0": self.betay0, "alphay0": self.alphay0,
            "Dx0": self.Dx0, "Dxp0": self.Dxp0,
            "Dy0": self.Dy0, "Dyp0": self.Dyp0,
            "emittance_x": self.emittance_x, "emittance_y": self.emittance_y,
            "x0": self.x0, "xp0": self.xp0, "y0": self.y0, "yp0": self.yp0,
            "delta_p": self.delta_p,
            "elements": [e.to_dict() for e in self.elements],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, d: dict) -> "Lattice":
        lat = cls()
        lat.mode      = d.get("mode", "linac")
        lat.linear    = d.get("linear", True)
        lat.betax0    = d.get("betax0", d.get("beta0", 1.0))
        lat.alphax0   = d.get("alphax0", d.get("alpha0", 0.0))
        lat.betay0    = d.get("betay0", 1.0)
        lat.alphay0   = d.get("alphay0", 0.0)
        lat.Dx0       = d.get("Dx0", 0.0);  lat.Dxp0 = d.get("Dxp0", 0.0)
        lat.Dy0       = d.get("Dy0", 0.0);  lat.Dyp0 = d.get("Dyp0", 0.0)
        lat.emittance_x = d.get("emittance_x", d.get("emittance", 1e-6))
        lat.emittance_y = d.get("emittance_y", 1e-6)
        lat.x0        = d.get("x0", 1e-3);  lat.xp0 = d.get("xp0", 0.0)
        lat.y0        = d.get("y0", 0.0);   lat.yp0 = d.get("yp0", 0.0)
        lat.delta_p   = d.get("delta_p", 0.0)
        lat.elements  = [Element.from_dict(e) for e in d.get("elements", [])]
        return lat

    @classmethod
    def from_json(cls, s: str) -> "Lattice":
        return cls.from_dict(json.loads(s))

    def to_elegant(self) -> str:
        lines = ["! RanMatrix — ELEGANT export", ""]
        seen = set()
        for e in self.elements:
            k = e.label.upper().replace(" ", "_")
            if k not in seen:
                lines.append(e.to_elegant_str()); seen.add(k)
        lines += ["", f"LATTICE: LINE=({', '.join(e.label.upper().replace(' ','_') for e in self.elements)})", "", "USE, LATTICE"]
        return "\n".join(lines)

    def to_bmad(self) -> str:
        lines = ["! RanMatrix — Bmad export", ""]
        seen = set()
        for e in self.elements:
            k = e.label.lower().replace(" ", "_")
            if k not in seen:
                lines.append(e.to_bmad_str()); seen.add(k)
        lines += ["", f"lat: line = ({', '.join(e.label.lower().replace(' ','_') for e in self.elements)})", "use, lat"]
        return "\n".join(lines)
