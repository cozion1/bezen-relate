# Big evaluation on cases_generated.json:
#   step 1 alone: is the right strength in the graph shortlist (top 3 / top 8)?
#   step 1 + 2:  does the agent pick the right strength, the right state, and a quote that is really in the message?
# Needs ANTHROPIC_API_KEY for step 2. Usage: python eval_big.py [graph file]
import json, sys, collections, concurrent.futures as cf
sys.argv = [sys.argv[0], "-", sys.argv[1] if len(sys.argv) > 1 else "bezen.rl"]
import read_person

cases = json.load(open("cases_generated.json", encoding="utf-8"))
full = {i: read_person.shortlist(x["text"], read_person.K) for i, x in enumerate(cases)}   # graph reads stay on one thread
short = {i: [c["strength"] for c in full[i]] for i in full}

def agent(i):
    x = cases[i]
    try:
        return i, read_person.decide(x["text"], full[i]) or {}
    except Exception as e:
        return i, {"error": str(e)[:80]}

with cf.ThreadPoolExecutor(6) as ex:
    answers = dict(ex.map(agent, range(len(cases))))

n = len(cases); c = collections.Counter(); by_state = collections.defaultdict(lambda: [0, 0]); misses = collections.Counter()
for i, x in enumerate(cases):
    a = answers[i]
    c["top3"] += x["strength"] in short[i][:3]
    c["top8"] += x["strength"] in short[i]
    ok_s = a.get("strength") == x["strength"]; ok_full = ok_s and a.get("state") == x["state"]
    c["strength"] += ok_s; c["full"] += ok_full; c["quote"] += bool(a.get("quote_verified")); c["errors"] += "error" in a
    by_state[x["state"]][0] += ok_full; by_state[x["state"]][1] += 1
    if not ok_s: misses[f"{x['strength']} -> {a.get('strength')}"] += 1

pct = lambda k: f"{c[k]}/{n} = {c[k]/n:.0%}"
print(f"cases {n}")
print(f"graph shortlist  top-3 {pct('top3')}   top-K {pct("top8")}")
print(f"agent strength   {pct('strength')}")
print(f"agent str+state  {pct('full')}")
print(f"quotes verified  {pct('quote')}   errors {c['errors']}")
for st, (ok, tot) in sorted(by_state.items()):
    print(f"  state {st:<9} {ok}/{tot} = {ok/tot:.0%}")
print("most common confusions:", misses.most_common(6))
print("sample error:", next((a["error"] for a in answers.values() if "error" in a), None)); json.dump({"n": n, **c}, open("eval_big_result.json", "w"), indent=1)
