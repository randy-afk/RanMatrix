# Phase Space & Twiss Plot

The centre panel contains three tabs. Phase Space and Twiss / Dispersion are described here.

---

## Phase Space tab

![Phase space — FODO ring](assets/full_gui.png)

The phase space view plots the beam ellipse in the (x, x') plane. Three types of objects are drawn:

| Object | Style | Description |
|---|---|---|
| Entrance ellipse | Orange dashed | Beam ellipse at the lattice entrance |
| Exit ellipse | Blue solid | Beam ellipse at the lattice exit |
| Ghost ellipses | Grey dashed | Ellipse at each element boundary |
| Particle | Orange dot with line | Trajectory of the test particle through the lattice |

The emittance ε, initial particle position x₀, and angle x'₀ are set in the toolbar above the plot.

**Ghost ellipses** trace the evolution of the beam ellipse as it passes through each element. Click a ghost ellipse to highlight the corresponding element in the lattice line and display its index in the status bar.

Toggle objects on or off with the **Ghosts** and **Particle** checkboxes in the toolbar.

A **Phase Space (y, y')** sub-tab shows the same view for the vertical plane.

### Ring mode behaviour

In Ring mode the entrance and exit ellipses are identical — they represent the periodic fixed-point solution. The ellipse does not change shape over many turns; only the particle position rotates around it.

### Linac mode behaviour

In Linac mode the entrance ellipse reflects the initial conditions from **Beam Setup** (β₀, α₀). The exit ellipse is the result of transporting those initial conditions through the full lattice.

---

## Twiss / Dispersion tab

![Twiss and dispersion — FODO cell](assets/twiss_dispersion.png)

A two-panel plot along the lattice coordinate s:

**Upper panel — Twiss functions**

- βx(s) — blue solid
- βy(s) — green solid
- αx(s) — blue dashed
- αy(s) — green dashed

**Lower panel — Dispersion**

- Dx(s) — blue solid
- Dy(s) — green solid

An **element bar** above the upper panel shows the lattice layout with colour-coded element blocks for spatial reference.

Toggle individual curves with the checkboxes in the control bar above the plot.

### Off-momentum overlay

The **Δp/p slider** applies a fractional momentum offset to the Twiss calculation. Moving the slider off zero adds a second set of ellipses to the Phase Space view (grey dashed) representing the off-momentum beam, and updates the dispersion panel accordingly. This allows visual inspection of chromatic beam size growth.

---

!!! tip "Comparing planes"
    In a symmetric FODO cell βx(s) and βy(s) are mirror images of each other. Adding sextupoles or asymmetric quads breaks this symmetry, which is visible immediately in the plot.
