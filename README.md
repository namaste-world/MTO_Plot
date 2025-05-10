# MTO Plot: Interactive Scholarly Timeline

An interactive Dash/Plotly visualization of citation and thematic relationships in the Music Theory Online (MTO) corpus. You can precompute the back-end data or skip straight to the front-end if you already have the JSON files in `public/`.

---

## Project Structure

```
.
├── app.py                   # Dash front-end application
├── backend/                 # Back-end pipeline modules & CLI
│   ├── __init__.py
│   ├── cli.py
│   ├── load_data.py
│   ├── citation.py
│   ├── semantic.py
│   ├── sharedref.py
│   ├── lineage.py
│   ├── institution.py
│   └── density.py
├── data/                    # Raw paper JSON files (input to back-end)
│   └── *.json
├── public/                  # Precomputed visualization data (output)
│   ├── nodes.json
│   ├── semantic_edges.json
│   ├── sharedref_edges.json
│   ├── lineage_edges.json
│   └── year_density.json
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

---

## Requirements

Create a Python 3.8+ virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

Contents of `requirements.txt`:

```text
numpy>=1.21
pandas>=1.3
scikit-learn>=1.0
torch>=1.7
sentence-transformers>=2.2
dash>=2.0
plotly>=5.0
tqdm>=4.0
```

---

## Running the Back-End

If you need to regenerate the JSON files in `public/`, run the back-end pipeline:

```bash
# From the project root directory
python3 -m backend.cli all \
  --json_dir data \
  --out_dir public \
  --top_k 5 \
  --sim_threshold 0.60
```

You can also run modules individually:

```bash
python3 -m backend.cli load      --json_dir data --out_dir public
python3 -m backend.cli citation  --json_dir data --out_dir public
python3 -m backend.cli semantic  --json_dir data --out_dir public --top_k 5 --sim_threshold 0.60
python3 -m backend.cli sharedref --json_dir data --out_dir public
python3 -m backend.cli lineage   --json_dir data --out_dir public
python3 -m backend.cli density   --json_dir data --out_dir public
```

Each command reads from `data/` and writes its output JSON into `public/`.

---

## Running the Front-End

Once `public/` contains:

* `nodes.json`
* `semantic_edges.json`
* `sharedref_edges.json`
* `lineage_edges.json`
* `year_density.json`

start the Dash app:

```bash
python3 app.py
```

Open your browser to [http://127.0.0.1:8050](http://127.0.0.1:8050) to:

* **Select** an edge type (semantic, shared-ref, or lineage)
* **Click** a node to reveal its local subgraph
* Press **Show All** to render every edge of the selected type
* Press **Reset View** to clear edges and show all nodes
* **Search** to highlight papers by title or author
* **Hover** any node for title and authors metadata
* **Zoom** and **pan** via scroll and drag, with a date-range slider
