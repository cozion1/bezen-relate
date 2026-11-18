# Validates every collected sentence in Cozio's order:
#   step 1: helpful or needs improvement?
#   step 2: if it needs improvement: lack or excess?
#   step 3: which balanced strength does it belong to?
# A sentence is VERIFIED when all the steps that apply match what its agent intended.
# Duplicates are removed first. The validator model reads sentences in batches, without being told the answer.
# Output: sentences_validated.json + a summary printed and saved to validate_summary.json
# Needs ANTHROPIC_API_KEY. Usage: python validate_sentences.py [validator model]
import json, os, re, sys, collections, urllib.request, concurrent.futures as cf

VALIDATOR = sys.argv[1] if len(sys.argv) > 1 else "claude-sonnet-5-5"
VAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_vault", "strengths")
BATCH = 12

rows = json.load(open("sentences_raw.json", encoding="utf-8"))

# --- dedupe: same normalized text, or near-identical (trigram Jaccard >= .85) inside one strength
norm = lambda s: re.sub(r"[^\w ]", "", s).strip()
grams = lambda s: {s[i:i + 3] for i in range(len(s) - 2)}
seen, kept, dup = {}, [], 0
for r in rows:
    n = norm(r["text"]); g = grams(n)
    if n in seen or any(len(g & h) / (len(g | h) or 1) >= .85 for h in seen.get(r["strength"] + "#", [])):
        dup += 1; continue
    seen[n] = 1; seen.setdefault(r["strength"] + "#", []).append(g); kept.append(r)
print(f"{len(rows)} collected, {dup} duplicates removed, {len(kept)} to validate", flush=True)

# --- the menu the validator sees: each strength with its description, no answers
menu = []
for f in sorted(os.listdir(VAULT)):
    t = open(os.path.join(VAULT, f), encoding="utf-8").read().splitlines()
    desc = next((l for l in t[4:] if l and not l.startswith(("#", "domain::"))), "")
    menu.append(f"- {f[:-3]}: {desc}")
MENU = "\n".join(menu)

def call(prompt):
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", method="POST",
        headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01", "content-type": "application/json"},
        data=json.dumps({"model": VALIDATOR, "max_tokens": 6000, "messages": [{"role": "user", "content": prompt}]}).encode())
    r = json.loads(urllib.request.urlopen(req, timeout=300).read())
    return next(b["text"] for b in r["content"] if b.get("type") == "text")

def judge(batch):
    items = "\n".join(f"{i}. {r['text']}" for i, r in enumerate(batch))
    prompt = (f"Balanced human strengths (each can be too little = lack, or too much = excess):\n{MENU}\n\n"
              f"Sentences people said:\n{items}\n\n"
              "For each sentence, answer in this order:\n"
              "1. kind: is it a HELPFUL sentence (balanced, the golden path) or does it NEED IMPROVEMENT?\n"
              "2. if it needs improvement: is it on the LACK side or the EXCESS side of a strength?\n"
              "3. strength: which balanced strength from the list does it belong to?\n"
              'Answer only JSON: [{"i": 0, "kind": "helpful|loaded", "state": "balanced|lack|excess", "strength": "<name>"}, ...]')
    try:
        out = call(prompt)
        ans = json.loads(re.search(r"\[.*\]", out, re.S).group(0))
        return [(batch[a["i"]], a) for a in ans if isinstance(a, dict) and 0 <= a.get("i", -1) < len(batch)]
    except Exception as e:
        print("  ! batch:", str(e)[:80], flush=True)
        return [(r, {"error": True}) for r in batch]

# shuffle deterministically so one batch mixes strengths and states
import random
random.Random(7).shuffle(kept)
batches = [kept[i:i + BATCH] for i in range(0, len(kept), BATCH)]
out = []
with cf.ThreadPoolExecutor(6) as ex:
    for res in ex.map(judge, batches):
        for r, a in res:
            r = dict(r)
            r["v_kind"], r["v_state"], r["v_strength"] = a.get("kind"), a.get("state"), a.get("strength")
            r["ok_kind"] = a.get("kind") == r["kind"]
            r["ok_state"] = r["ok_kind"] and a.get("state") == r["state"]
            r["ok_strength"] = a.get("strength") == r["strength"]
            r["verified"] = r["ok_state"] and r["ok_strength"]
            r["validator"] = VALIDATOR
            out.append(r)
json.dump(out, open("sentences_validated.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)

c = collections.Counter(); per_model = collections.defaultdict(collections.Counter)
for r in out:
    for k in ("ok_kind", "ok_state", "ok_strength", "verified"):
        c[k] += r[k]; per_model[r["model"]][k] += r[k]
    per_model[r["model"]]["n"] += 1
n = len(out)
summary = {"collected": len(rows), "duplicates": dup, "validated": n, "validator": VALIDATOR,
           "step1_kind": c["ok_kind"] / n, "step2_state": c["ok_state"] / n, "step3_strength": c["ok_strength"] / n,
           "verified": c["verified"] / n,
           "by_model": {m: {k: v[k] / v["n"] for k in ("ok_kind", "ok_state", "ok_strength", "verified")} | {"n": v["n"]}
                        for m, v in per_model.items()}}
json.dump(summary, open("validate_summary.json", "w"), indent=1)
print(json.dumps(summary, indent=1))
