# RanMatrix

**Interactive 6×6 beam optics explorer for accelerator physicists**

RanMatrix is a standalone desktop application for building and analysing accelerator lattices using the full 6×6 transfer matrix formalism. Drag elements onto a canvas, switch between Linac and Ring mode, and inspect the first- and second-order optics instantly — no simulation deck required.

![RanMatrix full GUI](assets/full_gui.png)

---

## Features

| Feature | Description |
|---|---|
| **6×6 R matrix** | Full first-order transfer matrix with colour-coded magnitude display |
| **T tensor** | 44 curated second-order terms grouped by Geometric, Chromatic, and Longitudinal |
| **Twiss (both planes)** | Courant-Snyder parameters βx, βy, αx, αy with 3×3 transport matrices |
| **Dispersion vector** | R₁₆, R₂₆, R₃₆, R₄₆, R₅₆ — Total, Element, and Cumulative |
| **Phase space** | Entrance/exit ellipses with ghost ellipses at every element boundary |
| **Twiss / Dispersion plot** | βx(s), βy(s), αx, αy, Dx, Dy along the lattice with Δp/p overlay |
| **Step mode** | Animate the phase-space ellipse element by element |
| **Export** | Copy matrix values or export the lattice |

---

## Quick Start

```bash
pip install PySide6 matplotlib numpy scipy
python main.py
```

See [Getting Started](quickstart.md) for a full walkthrough.

---

## Requirements

- Python ≥ 3.9
- PySide6
- matplotlib
- numpy
- scipy

---

*RanMatrix v1.0.0 — Randika Gamage*
