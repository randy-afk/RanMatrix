# Matrix Panel

The right panel shows computed optics in five tabs. The **Convention** selector at the top switches between coordinate orderings.

---

## R total

The full 6×6 transfer matrix from entrance to exit (Linac) or for one full turn (Ring).

![R total — FODO cell](assets/full_gui.png)

Matrix elements are colour-coded by magnitude:

- **Orange** — large positive values
- **Teal/dark** — values near zero
- **Red** — large negative values

Below the matrix:

| Field | Description |
|---|---|
| Tr(Rx) | Trace of the 2×2 horizontal sub-matrix |
| Tr(Ry) | Trace of the 2×2 vertical sub-matrix |
| det(R) | Determinant of the full 6×6 matrix (should be ±1) |
| R₅₆ | Longitudinal momentum compaction term |
| Qx, Qy | Fractional tunes (Ring mode only) |

A stability badge at the bottom of the tab confirms whether both planes satisfy |Tr| < 2.

---

## Element R

Single-click an element block in the lattice line to activate this tab. It shows two matrices:

![Element R — drift D2](assets/element_R.png)

**ELEMENT R** — the 6×6 matrix for the selected element alone.

**CUMULATIVE R (entrance → here)** — the product of all element matrices from the lattice entrance up to and including the selected element.

The element label (e.g. `[4] D2`) appears at the top left of the tab. This allows inspection of the optics at any intermediate point in the lattice without leaving the main window.

---

## T tensor

The second-order T_{ijk} tensor, displayed when **Physics: Nonlinear** is active.

![T tensor — FODO cell](assets/t_tensor.png)

44 curated terms are grouped into three categories:

**Geometric** — purely spatial second-order couplings (x², x·x', y², etc. → Δx, Δy, Δx', Δy')

**Chromatic** — momentum-dependent second-order corrections (x·δ, x'·δ, δ² → all transverse coordinates)

**Longitudinal** — second-order contributions to the time coordinate Δt (T₅₁₁, T₅₂₂, T₅₁₆, ...)

A **Show all non-zero** checkbox reveals the full set of non-zero T terms beyond the 44 curated ones.

!!! note "T terms require sextupoles or dipoles"
    For a pure FODO lattice with no sextupoles or dipoles, all geometric and chromatic T terms are zero. The longitudinal terms T₅₁₁ and T₅₂₂ are non-zero because quadrupoles contribute path-length effects to Δt.

---

## Twiss 3×3

The Courant-Snyder transport matrix for each transverse plane, expressed as a 3×3 matrix acting on the Twiss parameter vector (β, α, γ).

![Twiss 3×3 — x and y planes](assets/twiss_3x3.png)

Two sub-panels are shown: **x-plane** and **y-plane**. Each shows three columns:

| Column | Description |
|---|---|
| Total | Full lattice from entrance to exit |
| Element | Selected element only (single-click to activate) |
| Cumulative | Entrance to selected element |

Row and column headers label the Twiss parameters: β₀, α₀, γ₀ (entrance) and β_s, α_s, γ_s (exit).

---

## Dispersion

The 5-component dispersion column vector: R₁₆, R₂₆, R₃₆, R₄₆, R₅₆.

![Dispersion vector — FODO cell](assets/dispersion.png)

Three columns:

| Column | Description |
|---|---|
| Total | Dispersion from entrance to exit |
| Element | Dispersion contribution of the selected element only |
| Cumulative | Dispersion from entrance to selected element |

Each component is labelled with its physical meaning: R₁₆ = Dx, R₂₆ = Dx', R₃₆ = Dy, R₄₆ = Dy', R₅₆ = longitudinal path length–momentum term.

!!! note "Zero transverse dispersion without dipoles"
    R₁₆ through R₄₆ are zero for a lattice containing only quadrupoles and drifts. Dipoles are required to generate transverse dispersion. R₅₆ is non-zero even for a pure drift or FODO cell — it represents the path-length difference for off-momentum particles.
