# Physics Reference

---

## Coordinate convention

RanMatrix uses the 6-vector:

$$\mathbf{z} = (x,\ x',\ y,\ y',\ t,\ \delta)$$

where:

| Symbol | Meaning |
|---|---|
| x | Horizontal displacement from the reference orbit (m) |
| x' | Horizontal angle dx/ds (rad) |
| y | Vertical displacement (m) |
| y' | Vertical angle dy/ds (rad) |
| t | Time deviation from the reference particle (s), or −ℓ/c (path length) |
| δ | Fractional momentum deviation Δp/p |

This ordering follows the **ELEGANT / MAD-X** convention. The **Bmad** convention differs in the sign of coordinate 4 (y') — use the Convention selector in the matrix panel to switch.

---

## First-order transfer matrix

The 6×6 transfer matrix **R** relates the exit coordinates to the entrance coordinates to first order:

$$\mathbf{z}_\text{exit} = R\, \mathbf{z}_\text{entrance}$$

For a sequence of elements the total matrix is:

$$R_\text{total} = R_N \cdots R_2\, R_1$$

(element 1 is applied first, element N last — rightmost-first ordering).

Symplecticity requires det(R) = 1 for all conservative elements.

---

## Second-order T tensor

The second-order transport is:

$$z_i^\text{exit} = \sum_j R_{ij}\, z_j + \sum_{j \leq k} T_{ijk}\, z_j\, z_k$$

The T tensor has indices i (output coordinate, 1–6) and j, k (input coordinates, 1–6 with j ≤ k by symmetry). RanMatrix displays 44 physically significant terms grouped into Geometric, Chromatic, and Longitudinal categories.

T terms are non-zero when the lattice contains sextupoles, dipoles (edge focusing), or RF cavities. For a pure drift-quadrupole lattice only the longitudinal T₅ᵢⱼ terms (path-length corrections) can be non-zero.

---

## Courant-Snyder (Twiss) parameters

The 2×2 horizontal sub-matrix of R can be written as:

$$M_x = \begin{pmatrix} \cos\mu_x + \alpha_x \sin\mu_x & \beta_x \sin\mu_x \\ -\gamma_x \sin\mu_x & \cos\mu_x - \alpha_x \sin\mu_x \end{pmatrix}$$

where μx is the betatron phase advance, and γx = (1 + αx²)/βx.

The Courant-Snyder parameters are extracted from the one-turn matrix (Ring mode):

$$\cos\mu_x = \frac{\text{Tr}(M_x)}{2}, \quad \beta_x = \frac{M_{12}}{\sin\mu_x}, \quad \alpha_x = \frac{M_{11} - \cos\mu_x}{\sin\mu_x}$$

---

## Twiss 3×3 transport matrix

The Twiss parameters transform along the lattice according to the 3×3 matrix:

$$\begin{pmatrix} \beta_s \\ \alpha_s \\ \gamma_s \end{pmatrix} = \mathcal{M} \begin{pmatrix} \beta_0 \\ \alpha_0 \\ \gamma_0 \end{pmatrix}$$

where the transport matrix **M** is built from the 2×2 R block:

$$\mathcal{M} = \begin{pmatrix} R_{11}^2 & -2R_{11}R_{12} & R_{12}^2 \\ -R_{11}R_{21} & R_{11}R_{22}+R_{12}R_{21} & -R_{12}R_{22} \\ R_{21}^2 & -2R_{21}R_{22} & R_{22}^2 \end{pmatrix}$$

---

## Dispersion vector

The dispersion is driven by the 6th column of R (the δ-column). The 5-component vector shown in the Dispersion tab is:

$$\mathbf{d} = (R_{16},\ R_{26},\ R_{36},\ R_{46},\ R_{56})^\top$$

Physical interpretation: Dₓ = R₁₆ gives the horizontal displacement per unit momentum offset; R₅₆ gives the path length change per unit momentum offset (related to the momentum compaction factor α_c for rings).

---

## Stability condition

Both transverse planes must satisfy:

$$\left|\text{Tr}(M_x)\right| < 2 \quad \text{and} \quad \left|\text{Tr}(M_y)\right| < 2$$

If either condition is violated the lattice is unstable — the beam diverges on successive turns (Ring) or along the line (Linac with periodic cells).

---

## Fractional tunes (Ring mode)

The fractional betatron tunes are:

$$Q_x = \frac{\mu_x}{2\pi} = \frac{1}{2\pi}\arccos\!\left(\frac{\text{Tr}(M_x)}{2}\right), \qquad Q_y = \frac{\mu_y}{2\pi}$$

The integer part of the tune is not recoverable from a single one-turn matrix. RanMatrix reports only the fractional part 0 ≤ Q < 0.5.
