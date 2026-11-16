# Two-step reading of one message:
#   1. Graph shortlist (free, local): Relate vector index -> closest anchors -> their strengths, ranked in one Cypher query.
#   2. Agent decision (optional): an LLM picks strength + state from the shortlist only, and must quote the message;
#      the quote is checked in code. Without ANTHROPIC_API_KEY the shortlist is the answer.
# Usage: python read_person.py "message" [graph file]
import json, os, re, sys, relate
from fastembed import TextEmbedding

TEXT = sys.argv[1]
DB = sys.argv[2] if len(sys.argv) > 2 else "bezen.rl"
MODEL = os.environ.get("BEZEN_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
K = int(os.environ.get("BEZEN_K", "32"))
db = relate.Database(DB)
rows = lambda r: r.data() if callable(r.data) else r.data

_model = None
def shortlist(text, k=K):
    global _model
    _model = _model or TextEmbedding(MODEL)
    q = [float(x) for x in next(_model.embed([text]))]
    return rows(db.execute(f"""
        CALL db.index.vector.queryNodes("anchor_vec", {max(60, k * 25)}, vector($q, {len(q)}, FLOAT32)) YIELD node, score
        MATCH (s:Strength)-[:ANCHOR]->(node)
        WITH s, score ORDER BY score DESC
        WITH s, collect(score)[0..3] AS top
        WITH s, reduce(t = 0.0, x IN top | t + x) / size(top) AS fit
        ORDER BY fit DESC LIMIT {k}
        MATCH (s)-[:DOMAIN]->(d:Domain)
        OPTIONAL MATCH (s)-[:LACK]->(l:Sentence) OPTIONAL MATCH (s)-[:BALANCED]->(b:Sentence) OPTIONAL MATCH (s)-[:EXCESS]->(e:Sentence)
        RETURN s.name AS strength, s.title AS title, d.name AS domain, fit, l.text AS lack, b.text AS balanced, e.text AS excess
        ORDER BY fit DESC""", {"q": q}))

def decide(text, cands):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    import urllib.request
    menu = "\n".join(f"- {c['strength']}: lack \"{c['lack']}\" | balanced \"{c['balanced']}\" | excess \"{c['excess']}\"" for c in cands)
    prompt = (f"A person wrote:\n\"{text}\"\n\nCandidate strengths, each with three states:\n{menu}\n\n"
              "Pick ONE strength from the list and its state (lack, balanced or excess) that best explains what is "
              "really going on for this person. Quote the exact words from their message that show it. "
              'Answer only JSON: {"strength": "...", "state": "...", "quote": "...", "why": "one short sentence"}')
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", method="POST",
        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        data=json.dumps({"model": os.environ.get("BEZEN_LLM", "claude-haiku-5-5"), "max_tokens": 1000,
                         "messages": [{"role": "user", "content": prompt}]}).encode())
    resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
    out = next((b["text"] for b in resp.get("content", []) if b.get("type") == "text"), None)
    if out is None:
        raise RuntimeError(f"no text in reply: {[b.get('type') for b in resp.get('content', [])]} stop={resp.get('stop_reason')}")
    m = re.search(r"\{.*\}", out, re.S)
    if not m:
        raise RuntimeError(f"no JSON in reply (stop={resp.get('stop_reason')}): {out[:300]}")
    ans = json.loads(m.group(0))
    ans["quote_verified"] = ans.get("quote", "") in text            # exact quote, checked in code
    ans["in_shortlist"] = ans.get("strength") in [c["strength"] for c in cands]
    return ans

if __name__ == "__main__":
    cands = shortlist(TEXT)
    print("Shortlist from the graph:")
    for c in cands:
        print(f"  {c['fit']:.2f}  {c['strength']:<16} [{c['domain']}]")
    ans = decide(TEXT, cands)
    print("\nAgent decision:", json.dumps(ans, ensure_ascii=False) if ans else "(no ANTHROPIC_API_KEY set: shortlist only)")
