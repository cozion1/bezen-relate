# Meaning-based matcher with many anchors per strength:
#   every line in the strength note (description, characteristics, thinking, emotions, behaviors, beliefs, states)
#   is one vector labelled with its strength. Strength = the strength whose top-3 anchors are closest on average.
#   State = the closest of that strength's lack / balanced / excess sentences.
# BEZEN_MODEL may list several models, comma separated; their scores are averaged.
import os, numpy as np
from fastembed import TextEmbedding

MODELS = os.environ.get("BEZEN_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2").split(",")
VAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_vault", "strengths")

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
labels = np.array(labels)
NAMES = sorted(set(labels))

class Space:
    def __init__(self, model_name):
        self.m = TextEmbedding(model_name.strip())
        self.A = self.embed(anchors)
        self.S = {n: self.embed([t for _, t in st]) for n, st in states.items()}
    def embed(self, texts):
        v = np.array(list(self.m.embed(texts)))
        return v / np.linalg.norm(v, axis=1, keepdims=True)

SPACES = [Space(m) for m in MODELS]

def read(text):
    strength_score = {n: 0.0 for n in NAMES}
    qs = [sp.embed([text])[0] for sp in SPACES]
    for sp, q in zip(SPACES, qs):
        sims = sp.A @ q
        for n in NAMES:
            strength_score[n] += np.sort(sims[labels == n])[-3:].mean() / len(SPACES)
    best = max(strength_score, key=strength_score.get)
    state_sims = sum(sp.S[best] @ q for sp, q in zip(SPACES, qs)) / len(SPACES)
    i = int(state_sims.argmax())
    return float(strength_score[best]), best, states[best][i][0], states[best][i][1]
