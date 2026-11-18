# Two-step matcher, no model needed:
#   1. trait = best trigram overlap with the WHOLE trait note (description, thinking, emotions, behaviors, states)
#   2. state    = best trigram overlap among that trait's lack / balanced / excess sentences
import os, re, sys, relate

DB = sys.argv[1] if len(sys.argv) > 1 else "bezen.rl"
VAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_vault", "traits")
db = relate.Database(DB)
rows = lambda r: r.data() if callable(r.data) else r.data
norm = lambda s: re.sub(r"[^\w ]", " ", s)
grams = lambda s: {s[i:i + 3] for i in range(len(s) - 2)}
words = lambda s: {w for w in norm(s).split() if len(w) > 2}

PROFILE = {f[:-3]: open(os.path.join(VAULT, f), encoding="utf-8").read() for f in os.listdir(VAULT)}
PG = {k: grams(norm(v)) for k, v in PROFILE.items()}

def read(text):
    g = grams(norm(text))
    # containment: share of the message's trigrams found in the profile (profiles differ in length)
    trait = max(PG, key=lambda k: len(g & PG[k]) / (len(g) or 1))
    score = len(g & PG[trait]) / (len(g) or 1)
    best = None
    for st in ("LACK", "BALANCED", "EXCESS"):
        for r in rows(db.execute(f"MATCH (s:Trait {{name: $n}})-[:{st}]->(x:Sentence) RETURN x.text AS t", {"n": trait})):
            h = grams(norm(r["t"]))
            sc = len(g & h) / (len(g | h) or 1)
            if not best or sc > best[0]:
                best = (sc, st.lower(), r["t"])
    return score, trait, best[1], best[2]
