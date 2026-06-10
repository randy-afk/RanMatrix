# Linac vs Ring Mode

RanMatrix supports two operating modes selectable in the toolbar.

---

## Linac mode

In Linac mode the lattice is treated as a single-pass transport line. The transfer matrix is computed from the entrance to the exit of the full sequence.

The initial Twiss parameters are set by the user via **⚙ Beam Setup**:

| Parameter | Description |
|---|---|
| βx₀, βy₀ | Initial horizontal and vertical beta functions (m) |
| αx₀, αy₀ | Initial Courant-Snyder alpha parameters |
| Dx₀, Dy₀ | Initial dispersion (m) and dispersion prime (rad) |
| εx, εy | Beam emittance (mm·mrad) for ellipse scaling |
| x₀, x'₀, y₀, y'₀ | Initial particle coordinates for the trajectory marker |

The phase-space entrance ellipse (orange dashed) is constructed from these initial conditions. The exit ellipse (blue solid) is the transported result.

The R total tab shows the end-to-end 6×6 transfer matrix. Tr(Rx) and Tr(Ry) are displayed but Qx/Qy are not meaningful in single-pass mode.

---

## Ring mode

In Ring mode the lattice is closed — the exit is connected back to the entrance. RanMatrix solves for the **periodic Twiss solution** by finding the fixed point of the one-turn map.

The initial conditions are not user-settable in Ring mode. Instead, β, α, and γ at the entrance are derived from the one-turn matrix:

$$\beta = \frac{R_{12}}{\sin\mu}, \quad \alpha = \frac{R_{11} - \cos\mu}{\sin\mu}, \quad \mu = \arccos\left(\frac{\text{Tr}(M)}{2}\right)$$

The fractional tunes are:

$$Q_x = \frac{\mu_x}{2\pi}, \quad Q_y = \frac{\mu_y}{2\pi}$$

These are displayed in the status bar at the bottom of the window.

In Ring mode the entrance and exit ellipses in the Phase Space view are identical — they represent the same periodic solution.

---

## Stability

Regardless of mode, the stability condition is checked after every lattice change:

$$|\text{Tr}(M_x)| < 2 \quad \text{and} \quad |\text{Tr}(M_y)| < 2$$

The status bar shows `✓ STABLE` or `✗ UNSTABLE`. The R total panel also shows a colour-coded stability badge.

---

!!! warning "Ring mode with dispersive elements"
    In Ring mode with dipoles present, the periodic dispersion solution is computed automatically from R₁₆ and R₂₆ via the closed-orbit dispersion formula. In Linac mode, set Dx₀ manually in Beam Setup if the incoming beam has dispersion.
