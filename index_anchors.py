# Puts the meaning into the graph: every line of every trait note becomes an (:Anchor {text, vec})
# linked (:Trait)-[:ANCHOR]->(:Anchor), with a Relate vector index on Anchor.vec.
# Usage: python index_anchors.py [graph file]
import os, sys, time, relate
from fastembed import TextEmbedding

DB = sys.argv[1] if len(sys.argv) > 1 else "bezen.rl"
MODEL = os.environ.get("BEZEN_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
VAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_vault", "traits")

items = []
for f in os.listdir(VAULT):
    section = None
    for line in open(os.path.join(VAULT, f), encoding="utf-8").read().splitlines():
        if line.startswith("## "):
            section = line[3:].strip(); continue
        text = line.lstrip("->").strip()
        if len(text) >= 6 and not line.startswith(("#", "domain::", "state::")):
            items.append((f[:-3], section or "description", text))

t = time.time()
vecs = list(TextEmbedding(MODEL).embed([x[2] for x in items]))
dim = len(vecs[0])
db = relate.Database(DB)
db.execute("MATCH (a:Anchor) DETACH DELETE a")
for (trait, section, text), v in zip(items, vecs):
    db.execute(f"""MATCH (s:Trait {{name: $s}})
                   CREATE (s)-[:ANCHOR]->(:Anchor {{text: $t, section: $sec, vec: vector($v, {dim}, FLOAT32)}})""",
               {"s": trait, "t": text, "sec": section, "v": [float(x) for x in v]})
db.execute(f"""CREATE VECTOR INDEX anchor_vec IF NOT EXISTS FOR (a:Anchor) ON (a.vec)
               OPTIONS {{indexConfig: {{`vector.dimensions`: {dim}, `vector.similarity_function`: "cosine"}}}}""")
db.flush()
print(f"{len(items)} anchors ({dim} dims) indexed in {time.time()-t:.0f}s")
