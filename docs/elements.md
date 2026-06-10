# Element Palette

RanMatrix supports 16 element types. Click any element in the left panel to append it to the lattice. Double-click an element block in the canvas to edit its parameters.

---

## Basic

| Tag | Name | Parameters | Notes |
|---|---|---|---|
| `[D]` | Drift | `L` (m) | Free-space propagation |
| `[QF]` | Quad F | `K1` (m⁻²), `L` (m) | K1 > 0 focuses x, defocuses y |
| `[QD]` | Quad D | `K1` (m⁻²), `L` (m) | K1 < 0 defocuses x, focuses y |
| `[B]` | Dipole (sector) | `angle` (rad), `L` (m), `e1`, `e2` | Sector geometry with edge angles |
| `[BR]` | Dipole (rect) | `angle` (rad), `L` (m) | Rectangular magnet geometry |
| `[SOL]` | Solenoid | `Ks` (m⁻¹), `L` (m) | Integrated solenoid strength |

!!! note "K1 sign convention"
    Positive K1 focuses in the horizontal (x) plane and defocuses in the vertical (y) plane. Use negative K1 for a defocusing quad. The `[QF]` and `[QD]` labels are cosmetic — the physics is determined by the sign of K1 you enter.

!!! note "Solenoid Ks"
    `Ks` is the integrated solenoid field parameter `Ks = qBz/p`. Coupling between x and y planes is included in the 6×6 matrix.

---

## Higher Order

| Tag | Name | Parameters | Notes |
|---|---|---|---|
| `[SF]` | Sextupole | `K2` (m⁻³), `L` (m) | Contributes to T tensor geometric and chromatic terms |
| `[OC]` | Octupole | `K3` (m⁻⁴), `L` (m) | Third-order element (affects nonlinear tracking) |
| `[MP]` | Thin Multipole | `KnL[]` | Thin-lens multipole kicks up to arbitrary order |

---

## RF / Corrections

| Tag | Name | Parameters | Notes |
|---|---|---|---|
| `[RF]` | RF Cavity | `V` (MV), `phi` (deg), `freq` (MHz) | Longitudinal focusing; contributes to R₅₅, R₅₆, R₆₅ |
| `[KH]` | H Kicker | `angle` (mrad), `L` (m) | Horizontal orbit kick |
| `[KV]` | V Kicker | `angle` (mrad), `L` (m) | Vertical orbit kick |

---

## Apertures

| Tag | Name | Parameters | Notes |
|---|---|---|---|
| `[AC]` | Aperture (circ) | `r` (mm) | Circular aperture marker — displayed in canvas, no matrix effect |
| `[AR]` | Aperture (rect) | `x` (mm), `y` (mm) | Rectangular aperture marker |

Apertures do not contribute to the transfer matrix. They are purely geometric markers useful for layout bookkeeping.

---

## Special

| Tag | Name | Parameters | Notes |
|---|---|---|---|
| `[MX]` | Misaligned | `dx`, `dy`, `dφ` | Applies a coordinate offset to simulate a misalignment error |
| `[Mk]` | Marker | `name` | Zero-length marker; labels a position in the lattice |

---

## Editing elements

Double-click an element block to open its parameter dialog. Change any value and press **Enter** or click **Apply**. The matrix panel and plots update immediately.

To reorder elements, drag a block left or right in the lattice line. To remove an element, click the **×** button on its block.
