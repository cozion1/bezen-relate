# Builds the public sample vault: one Obsidian note per trait (32), per domain and per state.
# Source: the public traits page (bezenai.com/strengths). Nothing private goes in here.
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "BEZEN", "deploy_netlify", "strengths.html")
VAULT = os.path.join(HERE, "sample_vault")

html = open(SRC, encoding="utf-8").read()
block = html[html.index("const STRENGTHS = ["):]
block = block[block.index("["): block.index("\n];") + 2]
# The array is a JS literal; node turns it into JSON.
data = json.loads(subprocess.run(["node", "-e", f"console.log(JSON.stringify({block}))"],
                                 capture_output=True, text=True, encoding="utf-8", check=True).stdout)

DOMAINS = {"think": "Thinking", "relate": "Relating", "exec": "Doing", "influence": "Leading"}
for sub in ("traits", "domains", "states"):
    os.makedirs(os.path.join(VAULT, sub), exist_ok=True)

safe = lambda s: re.sub(r'[\\/:*?"<>|]', "-", s).strip()
domains = set()
for s in data:
    dom = DOMAINS.get(s["domain"], s["domain"].title())
    domains.add(dom)
    lines = [f"# {s['en']} ({s['name']})", "", f"domain:: [[{dom}]]", "", s["desc"], ""]
    for key in ("characteristics", "thinking", "emotions", "behaviors", "beliefs"):
        lines += [f"## {key}"] + [f"- {x}" for x in s.get(key, [])] + [""]
    for state in ("lack", "balanced", "excess"):
        lines += [f"## {state}", f"state:: [[{state}]]", f"> {s[state]}", ""]
    open(os.path.join(VAULT, "traits", safe(s["en"]) + ".md"), "w", encoding="utf-8").write("\n".join(lines))

for d in domains:
    open(os.path.join(VAULT, "domains", d + ".md"), "w", encoding="utf-8").write(f"# {d}\n")
for st, txt in (("lack", "Too little of the trait."), ("balanced", "The golden path."), ("excess", "Too much of the trait.")):
    open(os.path.join(VAULT, "states", st + ".md"), "w", encoding="utf-8").write(f"# {st}\n\n{txt}\n")
print(f"{len(data)} traits, {len(domains)} domains -> {VAULT}")
