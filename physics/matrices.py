"""
physics/matrices.py
-------------------
All 6×6 transfer matrices for every supported element type.
Pure functions — no side effects, no Qt, no global state.

Internal coordinate convention (ELEGANT/MAD-X style):
    u = [x, x', y, y', t, δ]
    where:
        x, y    = transverse positions (m)
        x', y'  = transverse angles (rad)  px/p0, py/p0 in paraxial limit
        t       = -Δl/c  (arrival time deviation, negative path length / c)
        δ       = Δp/p0  (fractional momentum deviation)

Index map:
    0=x  1=x'  2=y  3=y'  4=t  5=δ

Bmad convention: (x, px/p0, y, py/p0, z, pz/p0)
    where z = -c·t, pz/p0 = δ
    Transform to/from Bmad is a sign flip on coordinate 4 only.

Sign conventions:
    K1 > 0  →  horizontally focusing quad (defocusing in y)
    K1 < 0  →  horizontally defocusing quad (focusing in y)
    θ       →  full bend angle in x-plane (radians)
    e1, e2  →  entrance/exit pole-face angles
    L       →  path length (m)
    Ks      →  solenoid integrated strength B_s·L / (B·rho)
"""

from __future__ import annotations
import numpy as np
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Coordinate convention transforms
# ─────────────────────────────────────────────────────────────────────────────

# Internal index labels for clarity
IX  = 0   # x
IXP = 1   # x'
IY  = 2   # y
IYP = 3   # y'
IT  = 4   # t = -Δl/c
ID  = 5   # δ = Δp/p

COORD_LABELS = {
    "elegant": ["x", "x'", "y", "y'", "t", "δ"],
    "madx":    ["x", "px", "y", "py", "t", "pt"],
    "bmad":    ["x", "px/p₀", "y", "py/p₀", "z", "pz/p₀"],
}

def to_bmad(M: np.ndarray) -> np.ndarray:
    """
    Convert 6×6 matrix from internal (ELEGANT t,δ) to Bmad (z,pz) convention.
    z = -c·t  →  sign flip on row/col 4.
    """
    T = M.copy()
    T[4, :] = -T[4, :]
    T[:, 4] = -T[:, 4]
    return T

def from_bmad(M: np.ndarray) -> np.ndarray:
    return to_bmad(M)  # same transform (involution)


# ─────────────────────────────────────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────────────────────────────────────

def I6() -> np.ndarray:
    return np.eye(6)

def _k(K: float) -> float:
    """sqrt(|K|) — caller handles sign."""
    return np.sqrt(abs(K))


# ─────────────────────────────────────────────────────────────────────────────
# Drift
# ─────────────────────────────────────────────────────────────────────────────

def drift6(L: float) -> np.ndarray:
    """
    6×6 drift matrix.
    R56 = -L/γ² ≈ -L for ultra-relativistic (set γ→∞ → R56=0 in ultra-rel limit).
    We keep R56 = -L as a placeholder; correct value requires γ from beam.
    For display purposes we use the geometric term only.
    """
    M = I6()
    M[IX,  IXP] = L
    M[IY,  IYP] = L
    # Path length: t decreases (gets more negative) as particle drifts
    # R_{t,x'} = 0 for on-axis drift; R_{t,δ} = -L (ultra-rel approx)
    M[IT,  ID]  = -L   # momentum compaction contribution (ultra-rel)
    return M


# ─────────────────────────────────────────────────────────────────────────────
# Quadrupole
# ─────────────────────────────────────────────────────────────────────────────

def quad6(L: float, K1: float, thin: bool = False) -> np.ndarray:
    """
    6×6 quadrupole matrix.
    K1 > 0: focusing in x, defocusing in y.
    K1 < 0: defocusing in x, focusing in y.

    Thick: uses exact trigonometric/hyperbolic solutions.
    Thin:  L→0, K1L finite.
    """
    M = I6()

    if thin:
        K1L = K1 * L
        # x plane: thin lens kick
        M[IXP, IX]  = -K1L
        # y plane: opposite sign
        M[IYP, IY]  =  K1L
        return M

    if L == 0.0 or K1 == 0.0:
        return drift6(L)

    kx = _k(K1)
    ky = _k(K1)   # |K1| same magnitude both planes
    phix = kx * L
    phiy = ky * L

    if K1 > 0:
        # x: focusing (cos/sin), y: defocusing (cosh/sinh)
        M[IX,  IX]  =  np.cos(phix)
        M[IX,  IXP] =  np.sin(phix) / kx
        M[IXP, IX]  = -kx * np.sin(phix)
        M[IXP, IXP] =  np.cos(phix)

        M[IY,  IY]  =  np.cosh(phiy)
        M[IY,  IYP] =  np.sinh(phiy) / ky
        M[IYP, IY]  =  ky * np.sinh(phiy)
        M[IYP, IYP] =  np.cosh(phiy)
    else:
        # x: defocusing (cosh/sinh), y: focusing (cos/sin)
        M[IX,  IX]  =  np.cosh(phix)
        M[IX,  IXP] =  np.sinh(phix) / kx
        M[IXP, IX]  =  kx * np.sinh(phix)
        M[IXP, IXP] =  np.cosh(phix)

        M[IY,  IY]  =  np.cos(phiy)
        M[IY,  IYP] =  np.sin(phiy) / ky
        M[IYP, IY]  = -ky * np.sin(phiy)
        M[IYP, IYP] =  np.cos(phiy)

    # Path length term (R56 from quad: negligible for paraxial, set 0)
    M[IT, ID] = -L   # ultra-rel drift contribution
    return M


# ─────────────────────────────────────────────────────────────────────────────
# Sector dipole
# ─────────────────────────────────────────────────────────────────────────────

def dipole_sector6(L: float, theta: float,
                   e1: float = 0.0, e2: float = 0.0,
                   thin: bool = False) -> np.ndarray:
    """
    6×6 sector dipole with pole-face rotations.
    Bends in x-plane only.  y-plane is a drift.
    Includes dispersion (R16, R26) and path length (R51, R52, R56).
    """
    if thin or L == 0.0 or theta == 0.0:
        return I6()   # thin bend: identity in paraxial limit

    rho = L / theta
    phi = theta

    M = I6()

    # x-plane (bending plane)
    M[IX,  IX]  =  np.cos(phi)
    M[IX,  IXP] =  rho * np.sin(phi)
    M[IX,  ID]  =  rho * (1.0 - np.cos(phi))          # dispersion R16
    M[IXP, IX]  = -np.sin(phi) / rho
    M[IXP, IXP] =  np.cos(phi)
    M[IXP, ID]  =  np.sin(phi)                         # dispersion R26

    # y-plane: pure drift
    M[IY,  IYP] = L
    M[IYP, IYP] = 1.0

    # Path length / longitudinal
    M[IT,  IX]  = -np.sin(phi) / rho                   # R51 (geometry)  [sign: t = -Δl/c]
    M[IT,  IXP] = -(1.0 - np.cos(phi))                 # R52
    M[IT,  ID]  = -(phi - np.sin(phi)) * rho           # R56 (neg: longer path for higher p)
    # actually for ultra-rel: R56 = -(L/rho^2) * rho^2 * (theta - sin theta) ... 
    # standard formula: R56 = L/gamma^2 - rho*(theta-sin(theta)) ~ -rho*(theta-sin(theta)) ultra-rel
    # keeping geometric part:
    M[IT,  ID]  =  rho * (np.sin(phi) - phi)           # R56 geometric (positive for over-bending)

    # Pole-face rotations
    def pf(e: float) -> np.ndarray:
        P = I6()
        P[IXP, IX]  =  np.tan(e) / rho
        P[IYP, IY]  = -np.tan(e) / rho   # opposite sign in y
        return P

    return pf(e2) @ M @ pf(e1)


def dipole_rect6(L: float, theta: float, thin: bool = False) -> np.ndarray:
    """Rectangular dipole = sector + e1=e2=theta/2 pole faces."""
    if thin or L == 0.0 or theta == 0.0:
        return I6()
    return dipole_sector6(L, theta, e1=theta/2.0, e2=theta/2.0)


# ─────────────────────────────────────────────────────────────────────────────
# Solenoid
# ─────────────────────────────────────────────────────────────────────────────

def solenoid6(L: float, Ks: float) -> np.ndarray:
    """
    6×6 solenoid matrix.  Ks = k_s * L  where k_s = B_s / (2 * B_rho).
    Couples x-y planes.

    Uses the standard coupled transfer matrix.
    Reference: Wiedemann, "Particle Accelerator Physics", Ch. 10.
    """
    M = I6()
    if L == 0.0 or Ks == 0.0:
        return drift6(L)

    ks = Ks / L          # k_s per unit length
    phi = ks * L / 2.0   # half the Larmor rotation angle = Ks/2

    C  = np.cos(phi)
    S  = np.sin(phi)
    C2 = C * C
    S2 = S * S
    CS = C * S

    # Larmor frame rotation
    # Full 4×4 transverse block
    M[IX,  IX]  =  C2
    M[IX,  IXP] =  CS / ks
    M[IX,  IY]  =  CS
    M[IX,  IYP] =  S2 / ks

    M[IXP, IX]  = -ks * CS
    M[IXP, IXP] =  C2
    M[IXP, IY]  = -ks * S2
    M[IXP, IYP] =  CS

    M[IY,  IX]  = -CS
    M[IY,  IXP] = -S2 / ks
    M[IY,  IY]  =  C2
    M[IY,  IYP] =  CS / ks

    M[IYP, IX]  =  ks * S2
    M[IYP, IXP] = -CS
    M[IYP, IY]  = -ks * CS
    M[IYP, IYP] =  C2

    M[IT,  ID]  = -L   # ultra-rel drift
    return M


# ─────────────────────────────────────────────────────────────────────────────
# Sextupole / Octupole  (linear mode = identity; nonlinear = Phase 2)
# ─────────────────────────────────────────────────────────────────────────────

def sextupole6(L: float, K2: float, thin: bool = False) -> np.ndarray:
    """Linear mode: identity. Nonlinear: Phase 2."""
    M = drift6(L) if not thin else I6()
    return M

def octupole6(L: float, K3: float, thin: bool = False) -> np.ndarray:
    M = drift6(L) if not thin else I6()
    return M


# ─────────────────────────────────────────────────────────────────────────────
# RF cavity (thin, longitudinal kick only)
# ─────────────────────────────────────────────────────────────────────────────

def rf_cavity6(V: float, phi_s: float, f: float,
               E0: float = 1e9) -> np.ndarray:
    """
    Thin RF cavity — longitudinal focusing.
    V    : peak voltage (V)
    phi_s: synchronous phase (rad)
    f    : RF frequency (Hz)
    E0   : reference energy (eV)
    """
    c = 2.998e8
    k_rf = 2.0 * np.pi * f / c
    M = I6()
    e_over_E0 = V / E0   # dimensionless (both in same units: V and eV·e⁻¹)
    M[ID, IT] = e_over_E0 * k_rf * np.cos(phi_s)
    return M


# ─────────────────────────────────────────────────────────────────────────────
# Kickers (thin)
# ─────────────────────────────────────────────────────────────────────────────

def h_kicker6(theta_x: float) -> np.ndarray:
    """Horizontal thin kicker — identity (orbit offset tracked separately)."""
    return I6()

def v_kicker6(theta_y: float) -> np.ndarray:
    """Vertical thin kicker — identity."""
    return I6()


# ─────────────────────────────────────────────────────────────────────────────
# Thin multipole (general)
# ─────────────────────────────────────────────────────────────────────────────

def thin_multipole6(K1L: float = 0.0, K2L: float = 0.0,
                    K3L: float = 0.0) -> np.ndarray:
    """General thin multipole — linear (n=1) term only in linear mode."""
    M = I6()
    M[IXP, IX]  = -K1L
    M[IYP, IY]  =  K1L
    return M


# ─────────────────────────────────────────────────────────────────────────────
# Marker / identity
# ─────────────────────────────────────────────────────────────────────────────

def marker6() -> np.ndarray:
    return I6()


# ─────────────────────────────────────────────────────────────────────────────
# Matrix products and cumulative products
# ─────────────────────────────────────────────────────────────────────────────

def product(matrices: list[np.ndarray]) -> np.ndarray:
    """
    Left-to-right beam-order product.
    M_total = M_n @ ... @ M_1  (matrices[0] applied first = rightmost).
    """
    if not matrices:
        return I6()
    result = matrices[-1].copy()
    for M in reversed(matrices[:-1]):
        result = result @ M
    return result

def cumulative_products(matrices: list[np.ndarray]) -> list[np.ndarray]:
    """
    Cumulative products from entrance.
    result[0] = I  (entrance)
    result[k] = M_k @ ... @ M_1  (after element k)
    len = N+1
    """
    n = matrices[0].shape[0] if matrices else 6
    cum = [np.eye(n)]
    for M in matrices:
        cum.append(M @ cum[-1])
    return cum


# ─────────────────────────────────────────────────────────────────────────────
# Stability and Twiss extraction
# ─────────────────────────────────────────────────────────────────────────────

def is_stable(M: np.ndarray) -> bool:
    """
    Check transverse stability using the 4×4 block.
    Decouple x and y for stability check (works for uncoupled lattices).
    For coupled: check eigenvalues of the 4×4 symplectic block.
    """
    M4 = M[:4, :4]
    eigvals = np.linalg.eigvals(M4)
    # Stable if all eigenvalues lie on the unit circle
    return bool(np.all(np.abs(np.abs(eigvals) - 1.0) < 1e-4))

def trace_x(M: np.ndarray) -> float:
    """Trace of the 2×2 x-plane block."""
    return float(M[IX, IX] + M[IXP, IXP])

def trace_y(M: np.ndarray) -> float:
    """Trace of the 2×2 y-plane block."""
    return float(M[IY, IY] + M[IYP, IYP])

def tune_from_matrix(M: np.ndarray) -> tuple[Optional[float], Optional[float]]:
    """
    Compute (Qx, Qy) from one-turn 6×6 matrix.
    Returns (None, None) if unstable.
    """
    try:
        M4 = M[:4, :4]
        eigvals = np.linalg.eigvals(M4)
        # Sort into conjugate pairs by imaginary part
        phases = np.angle(eigvals)
        pos_phases = sorted([p for p in phases if p > 1e-10])
        if len(pos_phases) < 2:
            return None, None
        Qx = pos_phases[0] / (2.0 * np.pi)
        Qy = pos_phases[1] / (2.0 * np.pi)
        return Qx, Qy
    except Exception:
        return None, None

def twiss_from_one_turn(M: np.ndarray) -> Optional[dict]:
    """
    Extract Courant-Snyder parameters from one-turn 6×6 matrix.
    Returns dict with betax, alphax, gammax, betay, alphay, gammay, Qx, Qy.
    Returns None if unstable.
    """
    if not is_stable(M):
        return None

    Mx = M[:2, :2]
    My = M[2:4, 2:4]

    def cs_from_2x2(m):
        tr = m[0,0] + m[1,1]
        if abs(tr) >= 2.0:
            return None
        cos_mu = tr / 2.0
        sin_mu = np.sqrt(max(1.0 - cos_mu**2, 0.0))
        if abs(sin_mu) < 1e-12:
            return None
        beta  = m[0,1] / sin_mu
        alpha = (m[0,0] - m[1,1]) / (2.0 * sin_mu)
        gamma = -m[1,0] / sin_mu
        tune  = np.arccos(np.clip(cos_mu, -1, 1)) / (2.0 * np.pi)
        return beta, alpha, gamma, tune

    cx = cs_from_2x2(Mx)
    cy = cs_from_2x2(My)
    if cx is None or cy is None:
        return None

    return {
        "betax":  float(cx[0]), "alphax": float(cx[1]), "gammax": float(cx[2]), "Qx": float(cx[3]),
        "betay":  float(cy[0]), "alphay": float(cy[1]), "gammay": float(cy[2]), "Qy": float(cy[3]),
    }

def propagate_twiss(betax0: float, alphax0: float,
                    betay0: float, alphay0: float,
                    M: np.ndarray) -> dict:
    """
    Propagate Courant-Snyder parameters through 6×6 matrix M.
    Returns dict with betax, alphax, gammax, betay, alphay, gammay.
    """
    def transport(b0, a0, m):
        g0 = (1.0 + a0**2) / b0
        b1  =  m[0,0]**2 * b0 - 2*m[0,0]*m[0,1]*a0 + m[0,1]**2 * g0
        a1  = -(m[1,0]*m[0,0]*b0) + (m[0,0]*m[1,1]+m[0,1]*m[1,0])*a0 - m[0,1]*m[1,1]*g0
        g1  =  m[1,0]**2 * b0 - 2*m[1,0]*m[1,1]*a0 + m[1,1]**2 * g0
        return float(b1), float(a1), float(g1)

    Mx = M[:2, :2]
    My = M[2:4, 2:4]
    bx1, ax1, gx1 = transport(betax0, alphax0, Mx)
    by1, ay1, gy1 = transport(betay0, alphay0, My)
    return {
        "betax": bx1, "alphax": ax1, "gammax": gx1,
        "betay": by1, "alphay": ay1, "gammay": gy1,
    }

def dispersion_from_matrix(M: np.ndarray) -> dict:
    """Extract dispersion vector from 6×6 one-turn or transport matrix."""
    return {
        "Dx":   float(M[IX,  ID]),
        "Dxp":  float(M[IXP, ID]),
        "Dy":   float(M[IY,  ID]),
        "Dyp":  float(M[IYP, ID]),
        "R56":  float(M[IT,  ID]),
        "R51":  float(M[IT,  IX]),
        "R52":  float(M[IT,  IXP]),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Second-order T tensor
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# Second-order T tensor
# ─────────────────────────────────────────────────────────────────────────────

def _T_local_sextupole(K2L: float) -> np.ndarray:
    """Local T tensor for a thin sextupole."""
    T = np.zeros((6, 6, 6))
    T[IXP, IX,  IX]  = -K2L / 2.0
    T[IXP, IY,  IY]  =  K2L / 2.0
    T[IYP, IY,  IY]  =  K2L / 2.0   # sign: normal sext defocuses y
    T[IYP, IX,  IY]  = -K2L
    T[IYP, IY,  IX]  = -K2L
    return T


def _T_local_dipole(L: float, theta: float) -> np.ndarray:
    """
    Local T tensor for a thick sector dipole.
    Analytic second-order terms from the exact orbit expansion.
    Reference: Wiedemann "Particle Accelerator Physics" Vol.1, Chap. 4
               Forest "Beam Dynamics", Sec. 3.3

    Key terms included:
      T[x,  δ, δ]  = T166: second-order dispersion
      T[x', δ, δ]  = T266: second-order dispersion angle
      T[t,  x, x]  = T511: path length from x²
      T[t,  x, x'] = T512: path length from x·x'
      T[t,  x, δ]  = T516: path length from x·δ
      T[t,  x',δ]  = T526: path length from x'·δ
      T[t,  δ, δ]  = T566: second-order momentum compaction
    """
    if abs(theta) < 1e-12 or abs(L) < 1e-12:
        return np.zeros((6, 6, 6))

    rho = L / theta
    phi = theta
    C   = np.cos(phi)
    S   = np.sin(phi)

    T = np.zeros((6, 6, 6))

    # Second-order dispersion: x gets a δ² kick
    T[IX,  ID, ID]  =  rho * (1.0 - C)**2 / 2.0          # T166
    T[IXP, ID, ID]  =  S * (1.0 - C) / 2.0                # T266

    # Path length from transverse coordinates
    T[IT, IX,  IX]  = -S**2 / (2.0 * rho)                 # T511
    T[IT, IX,  IXP] =  S * (C - 1.0) / rho                # T512 (sym)
    T[IT, IXP, IX]  =  S * (C - 1.0) / rho                # T521
    T[IT, IXP, IXP] = -(phi - S*C) / 2.0                  # T522

    # Path length from x·δ and x'·δ coupling
    T[IT, IX,  ID]  = -S * (1.0 - C) / rho                # T516 (sym)
    T[IT, ID,  IX]  = -S * (1.0 - C) / rho                # T561
    T[IT, IXP, ID]  = -(1.0 - C)**2 / rho                 # T526 (sym)
    T[IT, ID,  IXP] = -(1.0 - C)**2 / rho                 # T562

    # Second-order momentum compaction
    T[IT, ID, ID]   =  rho * (S - phi) * (1.0 - C) / 2.0  # T566  (geometric)

    # Second-order x from x·x and x·y terms (from curved geometry)
    T[IX,  IX,  IX]  = -S**2 / (2.0 * rho)                # T111 curvature
    T[IXP, IX,  IX]  =  S * C / (2.0 * rho)               # T211
    T[IX,  IY,  IY]  =  S**2 / (2.0 * rho)                # T133 (sign flip vs x)
    T[IXP, IY,  IY]  = -S * C / (2.0 * rho)               # T233

    return T


def _T_local_drift(L: float) -> np.ndarray:
    """
    Local T tensor for a drift.
    Only contribution: path length from transverse angles (ultra-relativistic).
    T[t, x', x'] = -L/2  (T522: path length from x'²)
    T[t, y', y'] = -L/2  (T544)
    """
    T = np.zeros((6, 6, 6))
    T[IT, IXP, IXP] = -L / 2.0   # T522
    T[IT, IYP, IYP] = -L / 2.0   # T544
    return T


def compute_T_tensor(matrices: list[np.ndarray],
                     elements: list) -> np.ndarray:
    """
    Compute 6×6×6 second-order T tensor for the full lattice.
    Handles: sextupoles, dipoles, drifts.
    Quads, solenoids, kickers: no second-order terms in linear+thin approx.

    Transport formula:
      T_total[i,j,k] += R_out[i,a] * T_local[a,b,c] * R_in[b,j] * R_in[c,k]

    Parameters
    ----------
    matrices : list of 6×6 R matrices, one per element
    elements : list of Element objects (for type/param dispatch)
    """
    T = np.zeros((6, 6, 6))
    if not matrices or not elements:
        return T

    cum = cumulative_products(matrices)
    R_total = cum[-1]
    I6_mat  = np.eye(6)

    for n, elem in enumerate(elements):
        etype_name = elem.etype.name
        p = elem.params

        # Build local T for this element
        T_local = None

        if etype_name == 'SEXTUPOLE':
            K2L = p.get('K2', 0.0) * (p.get('L', 0.0) if not elem.thin else 1.0)
            if abs(K2L) > 1e-15:
                T_local = _T_local_sextupole(K2L)

        elif etype_name == 'THIN_MULTIPOLE':
            K2L = p.get('K2L', 0.0)
            if abs(K2L) > 1e-15:
                T_local = _T_local_sextupole(K2L)

        elif etype_name in ('DIPOLE_SECTOR', 'DIPOLE_RECT'):
            L     = p.get('L', 0.0)
            theta = p.get('theta', 0.0)
            if etype_name == 'DIPOLE_RECT':
                # Rectangular dipole = sector with e1=e2=theta/2
                # The body has the same theta but different pole-face angles
                pass  # use same formula; pole faces are thin linear
            if abs(theta) > 1e-12 and abs(L) > 1e-12:
                T_local = _T_local_dipole(L, theta)

        elif etype_name == 'DRIFT':
            L = p.get('L', 0.0)
            if abs(L) > 1e-12:
                T_local = _T_local_drift(L)

        if T_local is None:
            continue

        # Transport from element n to end:
        # R_in  = cumulative matrix up to and including element n (exit of n)
        # R_out = R_total @ inv(R_in)  [from exit of n to end]
        R_in = cum[n + 1]
        if n < len(matrices) - 1:
            try:
                R_out = R_total @ np.linalg.inv(R_in)
            except np.linalg.LinAlgError:
                R_out = I6_mat
        else:
            R_out = I6_mat

        # T_contrib[i,j,k] = R_out[i,a] * T_local[a,b,c] * R_in[b,j] * R_in[c,k]
        contrib = np.einsum('ia,abc,bj,ck->ijk', R_out, T_local, R_in, R_in)
        T += contrib

    return T


# Curated list of physically important T terms
# Format: (i, j, k, name, category, description)   — all indices 0-based
IMPORTANT_T_TERMS = [
    # ── Geometric sextupole terms (no δ) ──────────────────────────────────
    (0, 0, 0, "T₁₁₁", "Geometric", "x²  →  Δx  (geometric aberration)"),
    (0, 0, 1, "T₁₁₂", "Geometric", "x·x'  →  Δx"),
    (0, 1, 1, "T₁₂₂", "Geometric", "x'²  →  Δx"),
    (0, 2, 2, "T₁₃₃", "Geometric", "y²  →  Δx  (x-y coupling)"),
    (0, 2, 3, "T₁₃₄", "Geometric", "y·y'  →  Δx"),
    (0, 3, 3, "T₁₄₄", "Geometric", "y'²  →  Δx"),
    (1, 0, 0, "T₂₁₁", "Geometric", "x²  →  Δx'"),
    (1, 0, 1, "T₂₁₂", "Geometric", "x·x'  →  Δx'"),
    (1, 1, 1, "T₂₂₂", "Geometric", "x'²  →  Δx'"),
    (1, 2, 2, "T₂₃₃", "Geometric", "y²  →  Δx'"),
    (1, 2, 3, "T₂₃₄", "Geometric", "y·y'  →  Δx'"),
    (1, 3, 3, "T₂₄₄", "Geometric", "y'²  →  Δx'"),
    (2, 0, 2, "T₃₁₃", "Geometric", "x·y  →  Δy"),
    (2, 0, 3, "T₃₁₄", "Geometric", "x·y'  →  Δy"),
    (2, 1, 2, "T₃₂₃", "Geometric", "x'·y  →  Δy"),
    (2, 1, 3, "T₃₂₄", "Geometric", "x'·y'  →  Δy"),
    (2, 2, 2, "T₃₃₃", "Geometric", "y²  →  Δy  (geometric aberration)"),
    (2, 2, 3, "T₃₃₄", "Geometric", "y·y'  →  Δy"),
    (2, 3, 3, "T₃₄₄", "Geometric", "y'²  →  Δy"),
    (3, 0, 2, "T₄₁₃", "Geometric", "x·y  →  Δy'"),
    (3, 0, 3, "T₄₁₄", "Geometric", "x·y'  →  Δy'"),
    (3, 1, 2, "T₄₂₃", "Geometric", "x'·y  →  Δy'"),
    (3, 1, 3, "T₄₂₄", "Geometric", "x'·y'  →  Δy'"),
    (3, 2, 2, "T₄₃₃", "Geometric", "y²  →  Δy'"),
    (3, 2, 3, "T₄₃₄", "Geometric", "y·y'  →  Δy'"),
    (3, 3, 3, "T₄₄₄", "Geometric", "y'²  →  Δy'"),
    # ── Chromatic terms (involve δ, index 5) ──────────────────────────────
    (0, 0, 5, "T₁₁₆", "Chromatic", "x·δ  →  Δx  (chromatic x focusing)"),
    (0, 1, 5, "T₁₂₆", "Chromatic", "x'·δ  →  Δx  (chromatic beta beat)"),
    (0, 5, 5, "T₁₆₆", "Chromatic", "δ²  →  Δx  (2nd order dispersion x)"),
    (1, 0, 5, "T₂₁₆", "Chromatic", "x·δ  →  Δx'  (chromatic x' kick)"),
    (1, 1, 5, "T₂₂₆", "Chromatic", "x'·δ  →  Δx'  (chromatic beta beat)"),
    (1, 5, 5, "T₂₆₆", "Chromatic", "δ²  →  Δx'  (2nd order dispersion x')"),
    (2, 2, 5, "T₃₃₆", "Chromatic", "y·δ  →  Δy  (chromatic y focusing)"),
    (2, 3, 5, "T₃₄₆", "Chromatic", "y'·δ  →  Δy  (chromatic beta beat)"),
    (2, 5, 5, "T₃₆₆", "Chromatic", "δ²  →  Δy  (2nd order dispersion y)"),
    (3, 2, 5, "T₄₃₆", "Chromatic", "y·δ  →  Δy'  (chromatic y' kick)"),
    (3, 3, 5, "T₄₄₆", "Chromatic", "y'·δ  →  Δy'  (chromatic beta beat)"),
    (3, 5, 5, "T₄₆₆", "Chromatic", "δ²  →  Δy'  (2nd order dispersion y')"),
    # ── Longitudinal / path length ─────────────────────────────────────────
    (4, 0, 0, "T₅₁₁", "Long.",     "x²  →  Δt  (path length from x²)"),
    (4, 1, 1, "T₅₂₂", "Long.",     "x'²  →  Δt"),
    (4, 0, 5, "T₅₁₆", "Long.",     "x·δ  →  Δt"),
    (4, 1, 5, "T₅₂₆", "Long.",     "x'·δ  →  Δt"),
    (4, 5, 5, "T₅₅₆", "Long.",     "δ²  →  Δt  (2nd order R56)"),
    (5, 5, 5, "T₆₆₆", "Long.",     "δ²  →  Δδ  (nonlinear momentum compaction)"),
]

# Index labels for display (1-based)
COORD_NAMES_1BASED = ["1(x)", "2(x')", "3(y)", "4(y')", "5(t)", "6(δ)"]


# ─────────────────────────────────────────────────────────────────────────────
# Phase space ellipse (both planes)
# ─────────────────────────────────────────────────────────────────────────────

def ellipse_points(emittance: float, beta: float, alpha: float,
                   n_pts: int = 200) -> tuple[np.ndarray, np.ndarray]:
    """Generate (u, u') points on a Courant-Snyder ellipse."""
    gamma = (1.0 + alpha**2) / beta
    phi = np.linspace(0, 2*np.pi, n_pts)
    u  = np.sqrt(emittance * beta) * np.cos(phi)
    up = -np.sqrt(emittance / beta) * (alpha * np.cos(phi) + np.sin(phi))
    return u, up


def propagate_particle(x0: float, xp0: float,
                       y0: float, yp0: float,
                       matrices: list[np.ndarray]
                       ) -> dict:
    """
    Track a single particle through the lattice.
    Returns dict of lists (one per boundary, len=N+1).
    """
    u = np.array([x0, xp0, y0, yp0, 0.0, 0.0])
    xs,  xps = [u[0]], [u[1]]
    ys,  yps = [u[2]], [u[3]]
    ts,  ds  = [u[4]], [u[5]]
    for M in matrices:
        u = M @ u
        xs.append(u[0]); xps.append(u[1])
        ys.append(u[2]); yps.append(u[3])
        ts.append(u[4]); ds.append(u[5])
    return {"x": xs, "xp": xps, "y": ys, "yp": yps, "t": ts, "d": ds}
