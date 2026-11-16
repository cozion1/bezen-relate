# Meaning-based matcher: a small local multilingual model (no API, no cost, works offline after first download).
# Every strength state becomes one vector from "description + state sentence"; vectors are stored on the
# Sentence nodes in the graph, so the agent's memory and the match live in the same Relate file.
import os, sys, json, numpy as np, relate
from fastembed import TextEmbedding

DB = sys.argv[1] if len(sys.argv) > 1 else "bezen.rl"
MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
VAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_vault", "strengths")
db = relate.Database(DB)
rows = lambda r: r.data() if callable(r.data) else r.data
model = TextEmbedding(MODEL)
embed = lambda texts: np.array(list(model.embed(texts)))

desc = {}
for f in os.listdir(VAULT):
    lines = open(os.path.join(VAULT, f), encoding="utf-8").read().splitlines()
    desc[f[:-3]] = next((l for l in lines[4:] if l and not l.startswith(("#", "domain::"))), "")

ITEMS = [(r["s"], st.lower(), r["t"]) for st in ("LACK", "BALANCED", "EXCESS")
         for r in rows(db.execute(f"MATCH (s:Strength)-[:{st}]->(x:Sentence) RETURN s.name AS s, x.text AS t"))]
V = embed([f"{desc.get(s, '')} {t}" for s, _, t in ITEMS])
V /= np.linalg.norm(V, axis=1, keepdims=True)
for (s, st, t), v in zip(ITEMS, V):  # keep the vector in the graph
    db.execute("MATCH (x:Sentence {text: $t}) SET x.vec = $v", {"t": t, "v": json.dumps([round(float(a), 5) for a in v])})
db.flush()

def read(text):
    q = embed([text])[0]
    q /= np.linalg.norm(q)
    sims = V @ q
    i = int(sims.argmax())
    s, st, t = ITEMS[i]
    return float(sims[i]), s, st, t
