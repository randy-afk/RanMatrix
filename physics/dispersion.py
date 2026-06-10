"""
physics/dispersion.py
---------------------
Dispersion propagation and chromaticity computation.
All pure functions, no UI.
"""

import numpy as np
from typing import Optional
from .matrices import cumulative_products


def propagate_dispersion(D0: float, Dp0: float,
                         matrices3: list[np.ndarray]
                         ) -> tuple[list[float], list[float]]:
    """
    Propagate dispersion vector [D, D'] through 3×3 transfer matrices.
    Returns (Dx_list, Dpx_list) at each boundary (len = N+1).
    """
    u = np.array([0.0, 0.0, 1.0])   # δ=1 probe particle, x=x'=0
    # Initial dispersion as offset in u
    u[0] = D0
    u[1] = Dp0

    Dx_list  = [float(u[0])]
    Dpx_list = [float(u[1])]

    for M3 in matrices3:
        u = M3 @ u
        Dx_list.append(float(u[0]))
        Dpx_list.append(float(u[1]))

    return Dx_list, Dpx_list


def chromaticity_from_quad_scan(
    quads: list[dict],          # list of {"K1": ..., "L": ..., "beta": ..., "eta": ...}
    sextupoles: list[dict],     # list of {"K2L": ..., "beta": ..., "eta": ...}
    tune: float
) -> float:
    """
    Approximate natural chromaticity (without sextupoles).
    ξ = dQ/d(Δp/p) ≈ -1/(4π) ∫ K1(s) β(s) ds

    For each quad: contribution = K1 * L * beta / (4π)
    """
    xi = 0.0
    for q in quads:
        xi -= q["K1"] * q["L"] * q["beta"] / (4.0 * np.pi)

    # Sextupole correction (if any)
    for s in sextupoles:
        xi += s["K2L"] * s["beta"] * s["eta"] / (4.0 * np.pi)

    return xi


def solve_periodic_dispersion(matrices3: list[np.ndarray]
                              ) -> tuple[float, float]:
    """
    Solve for periodic dispersion in a ring.
    Find [Dx, Dpx] such that one-turn 3×3 matrix maps [Dx, Dpx, 1] to itself.

    (M3_total - I) · [Dx, Dpx] = -M3_col2 * 1
    where col2 is the δ-coupling column.
    """
    from .matrices import product as mat_product
    M3 = mat_product(matrices3) if matrices3 else np.eye(3)

    # Extract 2×2 block and coupling column
    A  = M3[:2, :2] - np.eye(2)     # (M_total - I) for [x, x']
    b  = -M3[:2, 2]                 # RHS: -δ coupling

    try:
        sol = np.linalg.solve(A, b)
        return float(sol[0]), float(sol[1])
    except np.linalg.LinAlgError:
        return 0.0, 0.0


def off_momentum_trajectory(x0: float, xp0: float, delta: float,
                             Dx: list[float], Dpx: list[float],
                             xs_on: list[float], xps_on: list[float]
                             ) -> tuple[list[float], list[float]]:
    """
    Off-momentum trajectory = on-momentum trajectory + delta * dispersion.

    xs_on  : on-momentum x positions at each boundary
    xps_on : on-momentum x' positions at each boundary
    Dx     : dispersion Dx at each boundary
    delta  : Δp/p
    """
    xs_off  = [x   + delta * d   for x,  d  in zip(xs_on,  Dx)]
    xps_off = [xp  + delta * dp  for xp, dp in zip(xps_on, Dpx)]
    return xs_off, xps_off
