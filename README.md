# 🔎 Post-Processing Ensemble Framework for Super-Resolution

[![Live Demo](https://img.shields.io/badge/Live-Demo-brightgreen)](https://tama0728.github.io/ESR_viewer)

_A web comparison tool for our Super-Resolution Post-Processing Ensemble Framework, originally forked from the [online test suite by Disney Research](https://tom94.net/data/publications/mueller18neural/interactive-viewer/)._

## Overview

This repository provides an interactive web viewer to visualize and compare the experimental results from our paper: **"Post-Processing Ensemble Framework for Balancing Fidelity and Perception in Super-Resolution"**.

## Updating the Web Viewer

To add new experimental results and update the viewer, use the `update_viewer.py` script. It scans the resulting images and automatically builds the necessary `data.js` and HTML structure.

```bash
python update_viewer.py
```
This updates the web viewer pages inside the `scenes/` directory.

### Viewing Results
Once updated, open `index.html` in a web browser to interact. You can effortlessly zoom, pan, and toggle to compare:
- **LR** (Low Resolution)
- **HR** (High Resolution)
- **SwinIR-C / PFT** (Structural Baselines)
- **SwinIR-RW / TSD-SR** (Perceptual Baselines)
- **Our1(edge)** (Edge-enhanced Output)
- **Our2(final)** (Final Output with Histogram Matching and Face Restoration)

---

## 👏🏻 Acknowledgments
* The interactive viewer template is borrowed and modified from [joeylitalien/interactive-viewer](https://github.com/joeylitalien/interactive-viewer), initially created by Disney Research.
* Contributions to the JS visualization logic by Jan Novák and Benedikt Bitterli.
