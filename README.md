# MTO Plot: Interactive Scholarly Timeline

This repository provides a Dash/Plotly front-end for exploring precomputed citation and thematic networks in the Music Theory Online (MTO) corpus. All back-end processing (JSON → nodes & edges) has been done; you can jump straight into running the visualization.

## Prerequisites

- Python 3.8+
- `public/` directory containing:
  - `nodes.json`
  - `semantic_edges.json`
  - `sharedref_edges.json`
  - `lineage_edges.json`
  - any other edge‐type JSON files you wish to explore

With your virtual environment active and dependencies installed, simply: run python3 app.py
This will start the Dash server on http://127.0.0.1:8050/. Open that URL in your browser.
