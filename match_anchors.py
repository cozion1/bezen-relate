# Meaning-based matcher with many anchors per strength:
#   every line in the strength note (description, characteristics, thinking, emotions, behaviors, beliefs, states)
#   is one vector labelled with its strength. Strength = the strength whose top-3 anchors are closest on average.
#   State = the closest of that strength's lack / balanced / excess sentences.
import os, sys, numpy as np
from fastembed import TextEmbedding

MODEL = os.environ.get("BEZEN_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
VAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_vault", "strengths")
model = TextEmbedding(MODEL)
def embed(texts):
    v = np.array(list(model.embed(texts)))
    return v / np.linalg.norm(v, axis=1, keepdims=True)

anchors, labels, states = [], [], {}
for f in os.listdir(VAULT):
    name, section = f[:-3], None
    for line in open(os.path.join(VAULT, f), encoding="utf-8").read().splitlines():
        if line.startswith("## "):
            section = line[3:].strip(); continue
        text = line.lstrip("->").strip()
        if len(text) < 6 or line.startswith(("#", "domain::", "state::")):
            continue
        anchors.append(text); labels.append(name)
        if section in ("lack", "balanced", "excess"):
            states.setdefault(name, []).append((section, text))
A = embed(anchors)
labels = np.array(labels)
S = {n: (st, embed([t for _, t in st])) for n, st in states.items()}

def read(text):
    q = embed([text])[0]
    sims = A @ q
    score = {n: np.sort(sims[labels == n])[-3:].mean() for n in set(labels)}
    best = max(score, key=score.get)
    st, vecs = S[best]
    i = int((vecs @ q).argmax())
    return float(score[best]), best, st[i][0], st[i][1]
