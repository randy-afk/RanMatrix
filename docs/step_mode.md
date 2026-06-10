# Step Mode

Step Mode animates the evolution of the phase-space ellipse as the beam passes through each element one at a time. It is primarily an educational tool for visualising how individual magnets transform the beam.

![Step mode — at entrance](assets/step_mode.png)

---

## Controls

| Control | Action |
|---|---|
| **⏮ Reset** | Return to the lattice entrance (Step 0) |
| **◀ Back** | Step backward by one element |
| **▶ Play** | Animate forward automatically at the current speed |
| **Step ▶** | Advance by one element |
| **⏭ End** | Jump to the last element |
| **Speed** slider | Adjust animation speed from slow to fast |

---

## Step display

The info bar below the controls shows:

```
Step 2 / 4  —  Drift  (s = 0.50 m)
```

This gives the current step index, total number of elements, the element name, and the s-position at the element exit.

Two small matrix displays — **Element R** and **Cumulative R** — appear below the info bar. These update at each step and show the 6×6 matrices for the current element and for the path from entrance to the current element, respectively.

---

## Phase space canvas

The main plot shows **Phase Space — step mode (x, x')** with three objects:

| Object | Style | Description |
|---|---|---|
| Entrance ellipse | Orange dashed | Fixed reference — the initial beam ellipse |
| Step ellipse | Blue solid | Current beam ellipse after N elements |
| Particle | Orange star | Current test particle position |

At Step 0 (entrance) the Step ellipse and Entrance ellipse are identical. As you step forward, the blue ellipse morphs — rotating and shearing — as each element applies its transfer matrix.

---

## Beam Setup in Step Mode

Click **⚙ Beam Setup** in the toolbar to open the initial conditions dialog. This sets:

- β₀, α₀ in both planes
- Dx₀, Dy₀ (initial dispersion) — relevant for Linac mode
- εx, εy (emittance) — scales the ellipse size
- x₀, x'₀, y₀, y'₀ — initial particle coordinates

Changes to Beam Setup reset Step Mode to Step 0 and rebuild the animation from the new initial conditions.

---

!!! tip "Educational use"
    Start with a simple `QF → D → QD → D` FODO cell in Ring mode. Press **Play** and observe how the quadrupoles squeeze the ellipse in one plane while expanding it in the other. The drift spaces rotate the ellipse. Over one full turn, the periodic solution returns to the starting ellipse.
