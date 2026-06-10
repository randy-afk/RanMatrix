# Getting Started

## Dependencies

RanMatrix requires four Python packages:

```bash
pip install PySide6 matplotlib numpy scipy
```

| Package | Purpose |
|---|---|
| PySide6 | GUI framework |
| matplotlib | Phase space and Twiss/Dispersion plots |
| numpy | Matrix arithmetic |
| scipy | SVD and linear algebra routines |

## Running RanMatrix

From the project directory:

```bash
python main.py
```

The application window opens immediately — no configuration file or simulation deck needed.

---

## Build your first FODO cell

This walkthrough builds a minimal FODO cell in Ring mode and verifies stability.

**1. Select Ring mode**

In the toolbar at the top, click **Ring**. The mode indicator turns orange.

**2. Add elements**

Click elements in the left palette to append them to the lattice line:

1. Click **[QF] Quad F** — a focusing quadrupole appears in the canvas
2. Click **[D] Drift** — a drift space follows
3. Click **[QD] Quad D** — a defocusing quadrupole
4. Click **[D] Drift** — a second drift to close the cell

You now have a 4-element FODO: `QF → D → QD → D`.

**3. Open the element editor**

Double-click any element block to open its parameter editor. Set:

- QF: `K1 = 1.2 m⁻²`, `L = 0.5 m`
- Drift: `L = 1.0 m`
- QD: `K1 = -1.2 m⁻²`, `L = 0.5 m`

**4. Observe Qx / Qy**

With Ring mode active and a stable lattice, the bottom status bar shows:

```
✓ STABLE   Qx = 0.1298   Qy = 0.1298
```

The right panel displays the 6×6 one-turn R matrix. Tr(Rx) and Tr(Ry) are shown below the matrix. Stability requires |Tr| < 2.

**5. Inspect the phase space**

Click the **Phase Space** tab in the centre panel. The entrance ellipse (orange dashed) and exit ellipse (blue solid) overlap in Ring mode — they are the same periodic solution.

**6. Open Twiss / Dispersion**

Click the **Twiss / Dispersion** tab to see βx(s), βy(s), αx, αy, Dx, and Dy plotted along the lattice length.

---

!!! tip "Undo / Redo"
    Use **← Undo** and **→ Redo** in the toolbar to step back through element additions and parameter changes.

!!! note "Drag to reorder"
    Elements in the lattice line can be dragged left or right to reorder them. Click the **×** button on an element to remove it.
