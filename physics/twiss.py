"""
physics/twiss.py
----------------
Twiss propagation along a lattice (both planes) and ring periodic solver.
All pure functions, 6×6.
"""

from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field
from typing import Optional
from .matrices import (
    propagate_twiss, twiss_from_one_turn, is_stable,
    cumulative_products, dispersion_from_matrix, I6
)


@dataclass
class TwissPoint:
    s:      float
    betax:  float
    alphax: float
    gammax: float
    phix:   float    # cumulative phase advance x
    betay:  float
    alphay: float
    gammay: float
    phiy:   float    # cumulative phase advance y
    Dx:     float = 0.0
    Dxp:    float = 0.0
    Dy:     float = 0.0
    Dyp:    float = 0.0
    R56_cum: float = 0.0


def propagate_twiss_along(betax0: float, alphax0: float,
                          betay0: float, alphay0: float,
                          matrices: list[np.ndarray],
                          s_positions: list[float],
                          Dx0: float = 0.0, Dxp0: float = 0.0,
                          Dy0: float = 0.0, Dyp0: float = 0.0,
                          ) -> list[TwissPoint]:
    """
    Propagate Twiss (both planes) and dispersion along lattice.
    Returns one TwissPoint per boundary (N+1 points).
    """
    # Entrance point
    gx0 = (1.0 + alphax0**2) / betax0
    gy0 = (1.0 + alphay0**2) / betay0

    points: list[TwissPoint] = []
    points.append(TwissPoint(
        s=s_positions[0],
        betax=betax0, alphax=alphax0, gammax=gx0, phix=0.0,
        betay=betay0, alphay=alphay0, gammay=gy0, phiy=0.0,
        Dx=Dx0, Dxp=Dxp0, Dy=Dy0, Dyp=Dyp0, R56_cum=0.0,
    ))

    betax_cur, alphax_cur = betax0, alphax0
    betay_cur, alphay_cur = betay0, alphay0
    phix_cum, phiy_cum = 0.0, 0.0
    R56_cum = 0.0

    # Dispersion propagation via 6-vector
    d_vec = np.array([Dx0, Dxp0, Dy0, Dyp0, 0.0, 1.0])

    for i, M in enumerate(matrices):
        # Twiss transport
        bx_prev, by_prev = betax_cur, betay_cur
        tw = propagate_twiss(betax_cur, alphax_cur, betay_cur, alphay_cur, M)
        betax_cur  = tw["betax"];  alphax_cur = tw["alphax"]
        betay_cur  = tw["betay"];  alphay_cur = tw["alphay"]

        # Phase advance x
        Mxx = M[:2, :2]
        if abs(Mxx[0,1]) > 1e-12 and bx_prev > 0 and betax_cur > 0:
            sin_dphi = Mxx[0,1] / np.sqrt(bx_prev * betax_cur)
            sin_dphi = np.clip(sin_dphi, -1.0, 1.0)
            dphi = np.arcsin(sin_dphi)
            if Mxx[0,0] * np.sqrt(bx_prev / betax_cur) < 0:
                dphi = np.pi - dphi
            phix_cum += dphi

        # Phase advance y
        Myy = M[2:4, 2:4]
        if abs(Myy[0,1]) > 1e-12 and by_prev > 0 and betay_cur > 0:
            sin_dphi = Myy[0,1] / np.sqrt(by_prev * betay_cur)
            sin_dphi = np.clip(sin_dphi, -1.0, 1.0)
            dphi = np.arcsin(sin_dphi)
            if Myy[0,0] * np.sqrt(by_prev / betay_cur) < 0:
                dphi = np.pi - dphi
            phiy_cum += dphi

        # Dispersion via 6-vector propagation
        d_vec = M @ d_vec
        R56_cum += M[4, 5]

        gx = (1.0 + alphax_cur**2) / betax_cur
        gy = (1.0 + alphay_cur**2) / betay_cur

        points.append(TwissPoint(
            s=s_positions[i+1],
            betax=betax_cur, alphax=alphax_cur, gammax=gx, phix=phix_cum,
            betay=betay_cur, alphay=alphay_cur, gammay=gy, phiy=phiy_cum,
            Dx=float(d_vec[0]), Dxp=float(d_vec[1]),
            Dy=float(d_vec[2]), Dyp=float(d_vec[3]),
            R56_cum=R56_cum,
        ))

    return points


def ring_periodic_twiss(M_total: np.ndarray,
                         matrices: list[np.ndarray],
                         s_positions: list[float],
                         ) -> Optional[list[TwissPoint]]:
    """
    Compute periodic Twiss for a ring.
    Returns None if lattice is unstable.
    """
    init = twiss_from_one_turn(M_total)
    if init is None:
        return None

    # Periodic dispersion: solve (I - M_total) · d = 0 for the δ-column
    # [Dx, Dxp, Dy, Dyp] from R-matrix columns
    Dx0  = float(M_total[0, 5])
    Dxp0 = float(M_total[1, 5])
    Dy0  = float(M_total[2, 5])
    Dyp0 = float(M_total[3, 5])

    # Solve properly: periodic dispersion from (I-M)·D_vec = M·[0,0,0,0,0,1]^T
    A = np.eye(4) - M_total[:4, :4]
    b = M_total[:4, 5]
    try:
        d_per = np.linalg.solve(A, b)
        Dx0, Dxp0, Dy0, Dyp0 = d_per
    except np.linalg.LinAlgError:
        pass   # fallback to R-column values

    return propagate_twiss_along(
        betax0=init["betax"], alphax0=init["alphax"],
        betay0=init["betay"], alphay0=init["alphay"],
        matrices=matrices, s_positions=s_positions,
        Dx0=float(Dx0), Dxp0=float(Dxp0),
        Dy0=float(Dy0), Dyp0=float(Dyp0),
    )
