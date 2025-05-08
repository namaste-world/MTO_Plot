from .load_data import slug
from sentence_transformers import SentenceTransformer
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors
import numpy as np, json, pathlib, datetime as dt, re

DATE4 = re.compile(r'^(\\d{4})')

def safe_year(date_iso:str)->int:
    m = DATE4.match(date_iso)
    return int(m.group(1)) if m else 1900

def build(papers, out:pathlib.Path, top_k=5, sim_th=.6, spacing=18):
    docs=[(p['abstract'] or '')+' '+' '.join(p['keywords']) for p in papers]
    model=SentenceTransformer('all-MiniLM-L6-v2')
    emb=model.encode(docs,batch_size=32,show_progress_bar=True,normalize_embeddings=True)

    pc1=PCA(1).fit_transform(emb).flatten()
    order=np.argsort(pc1)
    y={papers[idx]['id']:int(i*spacing) for i,idx in enumerate(order)}

    nn = NearestNeighbors(n_neighbors=top_k + 1, metric='cosine').fit(emb)
    dist,idx=nn.kneighbors(emb); sim=1-dist

    edges=[]
    years={p['id']:safe_year(p['date']) for p in papers}
    for i,(nbrs,sims) in enumerate(zip(idx,sim)):
        s=papers[i]['id']
        for j,c in zip(nbrs[1:],sims[1:]):
            if c<sim_th: continue
            t=papers[j]['id']
            edges.append({'source':s,'target':t,'type':'semantic',
                          'weight':round(float(c),4),
                          'yearLag':abs(years[s]-years[t])})

    nodes=[{**p,'yPx':y[p['id']], 'totalCitations':0} for p in papers]

    (out/'nodes.json').write_text(json.dumps(nodes,indent=2))
    (out/'semantic_edges.json').write_text(json.dumps(edges,indent=2))
