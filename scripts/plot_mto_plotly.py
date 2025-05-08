import json, pathlib, math
import pandas as pd
import plotly.graph_objects as go

# ---------------------------------------------------------------- paths
ROOT   = pathlib.Path(__file__).resolve().parents[1]      # project root
PUBLIC = ROOT / "public"
OUT_HTML = ROOT / "scripts" / "mto_timeline.html"

# ---------------------------------------------------------------- load nodes
nodes = pd.read_json(PUBLIC / "nodes.json")
nodes["date"] = pd.to_datetime(nodes["date"], errors="coerce")
nodes = nodes.dropna(subset=["date"])                     # toss bad
node_idx = {row.id: idx for idx, row in nodes.iterrows()}

# ---------------------------------------------------------------- helper
def load_edges(fname, color, width_fn, dash="solid"):
    fpath = PUBLIC / fname
    if not fpath.exists():
        print(f"[skip] {fname}")
        return None

    df = pd.read_json(fpath)
    if df.empty:
        return None

    xs, ys, src_ids, tgt_ids = [], [], [], []      # <- add tgt_ids
    for _, row in df.iterrows():
        s = node_idx.get(row.source); t = node_idx.get(row.target)
        if s is None or t is None: continue
        xs += [nodes.loc[s,"date"], nodes.loc[t,"date"], None]
        ys += [nodes.loc[s,"yPx"  ], nodes.loc[t,"yPx"  ], None]
        src_ids.append(row.source)
        tgt_ids.append(row.target)                 # <- new line

    if not xs:
        return None

    trace = go.Scattergl(
        x=xs, y=ys, mode="lines",
        line=dict(color=color,
                  width=width_fn(df.iloc[0]) if "weight" in df.columns else 1,
                  dash=dash),
        hoverinfo="skip",
        name=fname.replace("_edges.json", "")
    )
    # flags for JS interaction
    trace._isEdgeLayer = True
    trace._sourceIds   = src_ids
    trace._targetIds   = tgt_ids       # ✔ private attr passes validation
    return trace

# ---------------------------------------------------------------- traces
traces = [
    go.Scattergl(
        x=nodes.date, y=nodes.yPx, mode="markers",
        marker=dict(size=nodes.totalCitations.clip(lower=1).pow(.5)*4,
                    color="#4e79a7",
                    line=dict(width=.5,color="#222")),
        text=[f"<b>{t}</b><br>{', '.join(a)}"
              for t,a in zip(nodes.title,nodes.authors)],
        hoverinfo="text",
        name="Papers"
    )
]

EDGE_LAYERS = [
    ("semantic_edges.json",  "rgba(78,121,167,0.4)",      lambda r: r["weight"] * 5,         "solid"),
    ("sharedref_edges.json", "rgba(80,80,80,0.3)",       lambda r: math.sqrt(r["weight"]),  "dot"),
    ("lineage_edges.json",   "rgba(200,200,200,0.3)",     lambda r: 1,                       "dash"),
]

for args in EDGE_LAYERS:
    tr = load_edges(*args)
    if tr: traces.append(tr)

# ---------------------------------------------------------------- layout
dates = nodes.date
layout = dict(
    title="MTO – Interactive Citation · Similarity · Affiliation Timeline",
    xaxis=dict(title="Publication Date",
               range=[dates.min(), dates.max()],
               rangeslider=dict(visible=True, thickness=0.05),
               tickformat="%Y", showgrid=False),
    yaxis=dict(visible=False, range=[-20, nodes.yPx.max()+20]),
    height=800, hovermode="closest", showlegend=True,
    margin=dict(l=40,r=40,t=80,b=40)     # extra top for button bar
)

fig = go.Figure(traces, layout)



# -------------------- add updatemenu buttons ------------------------------
edge_indices = {tr.name: i for i,tr in enumerate(fig.data) if getattr(tr, "_isEdgeLayer", False)}

buttons = [dict(label="All", method="update",
                args=[{"visible":[True]*len(fig.data)},
                      {"title":"All layers"}])]
for name, idx in edge_indices.items():
    vis = [True] + [False]*(len(fig.data)-1)
    vis[idx] = True  # keep that layer on
    buttons.append(dict(label=name, method="update",
                        args=[{"visible":vis},{"title":f"Layer: {name}"}]))

fig.update_layout(updatemenus=[dict(
    type="buttons", direction="right", y=1.18, x=0.5, xanchor="center",
    buttons=buttons, pad={"t":0,"r":10}
)])

# -------------------- export HTML (partial) -------------------------------
html = fig.to_html(include_plotlyjs="cdn", full_html=False)
(OUT_HTML).write_text(html)       # write first
print("✓  Base HTML written; appending custom JS …")

JS = """
<!-- search UI ---------------------------------------------------------->
<div style="margin:8px 0;display:flex;gap:6px;align-items:center">
  <input id="searchBox" type="text" placeholder="Search title or author"
         style="flex:1;padding:4px 6px;font-size:14px">
  <button id="searchBtn" style="padding:4px 10px;font-size:14px">Go</button>
</div>

<script>
document.addEventListener("DOMContentLoaded", () => {
  const gd   = document.querySelector("div.plotly-graph-div");
  const node = gd.data[0];                       // scattergl trace with nodes
  const edgeCache = {};
  const big = 18, nbrSize = 12, red = "rgb(220,30,30)";

  /* ---------- click: reveal edges + tint neighbours --------------- */
  gd.on("plotly_click", ev => {
    const pt = ev.points[0];
    if (!pt || pt.fullData !== node) return;
    revealEdgesAndTint(pt.pointIndex);
  });

  /* ---------- search: enlarge only ------------------------------- */
  const box = document.getElementById("searchBox");
  document.getElementById("searchBtn").onclick =
  box.onkeydown = e => {
    if (e.type === "keydown" && e.key !== "Enter") return;
    const q = box.value.toLowerCase().trim();
    if (!q) return;
    const idx = node.text.findIndex(t => t.toLowerCase().includes(q));
    if (idx === -1) { alert("No match!"); return; }
    highlightNode(idx);          // red + big, nothing else
  };

  /* ---------- helpers -------------------------------------------- */
  function extractId(html){ return html.match(/<b>(.*?)<\\/b>/)[1]; }

  function highlightNode(idx){
    const sizes = node.marker.size.slice(),
          colors= node.marker.color.slice();
    sizes[idx]  = big;
    colors[idx] = red;
    Plotly.restyle(gd, {"marker.size":[sizes], "marker.color":[colors]}, [0]);
  }

  function revealEdgesAndTint(idx){
    const id = extractId(node.text[idx]);
    if (edgeCache[id]) return;                 // already handled

    const xs=[], ys=[], neighbours=new Set();

    gd.data.forEach(tr=>{
      if(!tr._isEdgeLayer || tr.visible === false) return; // respect toggle
      const segCount = tr._sourceIds.length;               // one id per segment
      for(let seg=0; seg<segCount; seg++){
        if(tr._sourceIds[seg] !== id) continue;
        const i = seg * 3;                   // base index in x/y
        xs.push(tr.x[i], tr.x[i+1], null);
        ys.push(tr.y[i], tr.y[i+1], null);
        neighbours.add(tr._targetIds[seg]);
      }
    });

    if (xs.length){
      Plotly.addTraces(gd, {
        x:xs, y:ys, mode:"lines",
        line:{color:"rgba(255,0,0,.7)", width:1},
        hoverinfo:"skip", showlegend:false
      });
      edgeCache[id] = true;
    }

    tintNeighbours(neighbours);
  }

  function tintNeighbours(idSet){
    if (!idSet.size) return;
    const sizes=node.marker.size.slice(),
          colors=node.marker.color.slice();
    idSet.forEach(id=>{
      const i = node.text.findIndex(t => extractId(t) === id);
      if(i === -1) return;
      sizes[i]  = Math.max(sizes[i], nbrSize);
      colors[i] = red;
    });
    Plotly.restyle(gd, {"marker.size":[sizes], "marker.color":[colors]}, [0]);
  }
});
</script>
"""




with OUT_HTML.open("a") as f: f.write(JS)
print(f"✓  Open {OUT_HTML} in your browser.")
