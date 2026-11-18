# Builds a larger test set: for every trait and state, a model writes everyday Hebrew messages
# a real person might send, WITHOUT reusing the words of the trait sentences. Then a lexical filter
# drops any message that still overlaps too much, so the test measures meaning, not word copying.
# Needs ANTHROPIC_API_KEY. Output: cases_generated.json
import json, os, re, urllib.request, concurrent.futures as cf

VAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_vault", "traits")
PER_STATE = int(os.environ.get("PER_STATE", "3"))
MODEL = os.environ.get("GEN_MODEL", "claude-sonnet-5-5")

def call(prompt):
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", method="POST",
        headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01", "content-type": "application/json"},
        data=json.dumps({"model": MODEL, "max_tokens": 2000, "messages": [{"role": "user", "content": prompt}]}).encode())
    r = json.loads(urllib.request.urlopen(req, timeout=120).read())
    return next(b["text"] for b in r["content"] if b.get("type") == "text")

def note(name):
    return open(os.path.join(VAULT, name + ".md"), encoding="utf-8").read()

def gen(name):
    prompt = (f"Here is a description of a human trait and its three states:\n\n{note(name)}\n\n"
              f"Write {PER_STATE} different short messages in everyday Israeli Hebrew for EACH state (lack, balanced, excess): "
              "things a real person might write to a friend, a colleague, a shop or a support chat, in which that state shows. "
              "Rules: do NOT reuse the distinctive words of the description or of the quoted state sentences; "
              "vary the setting (work, home, shopping, school, health); 1-2 sentences each; no names of the trait. "
              'Answer only JSON: {"lack": ["..."], "balanced": ["..."], "excess": ["..."]}')
    out = call(prompt)
    d = json.loads(re.search(r"\{.*\}", out, re.S).group(0))
    return [(t, name, st) for st in ("lack", "balanced", "excess") for t in d.get(st, [])[:PER_STATE]]

grams = lambda s: {s[i:i + 3] for i in range(len(s) - 2)}
norm = lambda s: re.sub(r"[^\w ]", " ", s)

if __name__ == "__main__":
    names = sorted(f[:-3] for f in os.listdir(VAULT))
    cases = []
    with cf.ThreadPoolExecutor(6) as ex:
        for res in ex.map(gen, names):
            cases += res
    kept = []
    for t, name, st in cases:
        sentences = re.findall(r"^> (.*)$", note(name), re.M)
        overlap = max(len(grams(norm(t)) & grams(norm(s))) / (len(grams(norm(t))) or 1) for s in sentences)
        if overlap < 0.35:
            kept.append({"text": t, "trait": name, "state": st, "overlap": round(overlap, 2)})
    json.dump(kept, open("cases_generated.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"generated {len(cases)}, kept {len(kept)} after the overlap filter")
