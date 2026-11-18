# One agent per balanced strength. For each of the six dimensions (thoughts, emotions, sensations,
# complex behaviors, limiting beliefs, blockers) it asks a model for HELPFUL sentences (the balanced
# state), and for EACH helpful sentence several "needs improvement" sentences on the lack side and
# on the excess side. Every loaded sentence keeps a link to the helpful sentence it belongs to.
# Output: sentences_raw.json  [{id, strength, dimension, kind: helpful|loaded, state: balanced|lack|excess,
#                              text, helpful_id, model}]
# Needs ANTHROPIC_API_KEY. Usage: python sentence_agents.py [models comma separated]
import json, os, re, sys, urllib.request, concurrent.futures as cf

VAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_vault", "strengths")
MODELS = (sys.argv[1] if len(sys.argv) > 1 else "claude-haiku-5-5,claude-sonnet-5-5,claude-opus-5-5").split(",")
HELPFUL = int(os.environ.get("HELPFUL", "3"))     # helpful sentences per dimension
LOADED = int(os.environ.get("LOADED", "3"))       # lack sentences AND excess sentences per helpful sentence
DIMENSIONS = {"thoughts": "מחשבות", "emotions": "רגשות", "sensations": "תחושות",
              "behaviors": "התנהגויות מורכבות", "beliefs": "אמונות מגבילות", "blockers": "חסמים"}

def call(model, prompt):
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", method="POST",
        headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01", "content-type": "application/json"},
        data=json.dumps({"model": model, "max_tokens": 16000, "messages": [{"role": "user", "content": prompt}]}).encode())
    r = json.loads(urllib.request.urlopen(req, timeout=600).read())
    return next(b["text"] for b in r["content"] if b.get("type") == "text")

def agent(job):
    name, model = job
    note = open(os.path.join(VAULT, name + ".md"), encoding="utf-8").read()
    dims = "; ".join(f"{k} ({v})" for k, v in DIMENSIONS.items())
    prompt = (f"You are the sentence collector for one balanced human strength. Its description:\n\n{note}\n\n"
              f"For EACH of the six dimensions: {dims}\n"
              f"write {HELPFUL} different HELPFUL sentences: what a person says, in the first person, when this strength "
              "is balanced in that dimension (the golden path).\n"
              f"For EACH helpful sentence, write {LOADED} 'needs improvement' sentences on the LACK side (too little of the "
              f"strength) and {LOADED} on the EXCESS side (too much of it), each one a version of the same situation as its helpful sentence.\n"
              "All in natural, everyday Israeli Hebrew, as people really say them (work, home, family, school, shopping, health). "
              "One sentence each. Vary the wording; do not copy sentences from the description.\n"
              'Answer only JSON: {"thoughts": [{"helpful": "...", "lack": ["..."], "excess": ["..."]}, ...], "emotions": [...], ...}')
    try:
        out = call(model, prompt)
        d = json.loads(re.search(r"\{.*\}", out, re.S).group(0))
    except Exception as e:
        print(f"  ! {name} / {model}: {str(e)[:80]}", flush=True)
        return []
    rows, short = [], model.replace("claude-", "").split("-")[0]
    for dim in DIMENSIONS:
        for i, item in enumerate(d.get(dim) or []):
            if not isinstance(item, dict) or not item.get("helpful"):
                continue
            hid = f"{name}|{dim}|{short}|{i}"
            rows.append({"id": hid, "strength": name, "dimension": dim, "kind": "helpful", "state": "balanced",
                         "text": item["helpful"].strip(), "helpful_id": hid, "model": model})
            for st in ("lack", "excess"):
                for j, t in enumerate(item.get(st) or []):
                    if isinstance(t, str) and t.strip():
                        rows.append({"id": f"{hid}|{st}|{j}", "strength": name, "dimension": dim, "kind": "loaded",
                                     "state": st, "text": t.strip(), "helpful_id": hid, "model": model})
    print(f"  {name:<16} {short:<7} {len(rows)}", flush=True)
    return rows

if __name__ == "__main__":
    names = sorted(f[:-3] for f in os.listdir(VAULT))
    jobs = [(n, m) for m in MODELS for n in names]
    rows = []
    with cf.ThreadPoolExecutor(6) as ex:
        for r in ex.map(agent, jobs):
            rows += r
    json.dump(rows, open("sentences_raw.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"total {len(rows)} sentences ({sum(r['kind']=='helpful' for r in rows)} helpful) from {len(MODELS)} models")
