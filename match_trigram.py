# Baseline matcher: character trigrams against every trait sentence in the graph.
import re, sys, relate

db = relate.Database(sys.argv[1] if len(sys.argv) > 1 else "bezen.rl")
rows = lambda r: r.data() if callable(r.data) else r.data
grams = lambda s: {s[i:i + 3] for i in range(len(s) - 2)} if s else set()
norm = lambda s: re.sub(r"[^\w ]", "", s)
SENTENCES = [(r["s"], st.lower(), r["t"]) for st in ("LACK", "BALANCED", "EXCESS")
             for r in rows(db.execute(f"MATCH (s:Trait)-[:{st}]->(x:Sentence) RETURN s.name AS s, x.text AS t"))]

def read(text):
    g = grams(norm(text))
    return max(((len(g & grams(norm(t))) / (len(g | grams(norm(t))) or 1), s, st, t) for s, st, t in SENTENCES))
