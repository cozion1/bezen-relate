# Any Obsidian vault -> a Relate graph, in one file.
#   note            -> node, labelled by its top folder ("traits" -> :Trait)
#   key:: [[x]]     -> typed edge (note)-[:KEY]->(x)
#   [[x]]           -> (note)-[:LINKS]->(x)
#   "> quote" under "## heading" -> (note)-[:HEADING]->(:Sentence {text})
# Usage: python vault_to_graph.py <vault folder> <graph file>
import os, re, sys, time, relate

VAULT = sys.argv[1] if len(sys.argv) > 1 else "sample_vault"
OUT = sys.argv[2] if len(sys.argv) > 2 else "bezen.rl"
FIELD = re.compile(r"^(\w+)::\s*\[\[([^\]|#]+)", re.M)
LINK = re.compile(r"\[\[([^\]|#]+)")
label_of = lambda folder: re.sub(r"[^A-Za-z]", "", folder.rstrip("s").title()) or "Note"

notes = {}
for root, _, files in os.walk(VAULT):
    if ".obsidian" in root:
        continue
    folder = os.path.relpath(root, VAULT).split(os.sep)[0]
    for f in files:
        if f.endswith(".md"):
            text = open(os.path.join(root, f), encoding="utf-8", errors="replace").read()
            notes[f[:-3]] = (label_of(folder) if folder != "." else "Note", text)

t = time.time()
if os.path.exists(OUT):
    os.remove(OUT)
db = relate.Database(OUT)
for name, (label, text) in notes.items():
    title = next((l[2:].strip() for l in text.splitlines() if l.startswith("# ")), name)
    db.execute(f"CREATE (:{label} {{name: $n, title: $t}})", {"n": name, "t": title})

edges = sentences = 0
for name, (label, text) in notes.items():
    typed = set()
    for key, target in FIELD.findall(text):
        target = target.strip()
        if target in notes:
            db.execute(f"MATCH (a {{name: $a}}), (b {{name: $b}}) CREATE (a)-[:{key.upper()}]->(b)", {"a": name, "b": target})
            typed.add(target); edges += 1
    for target in set(m.strip() for m in LINK.findall(text)) - typed:
        if target in notes and target != name:
            db.execute("MATCH (a {name: $a}), (b {name: $b}) CREATE (a)-[:LINKS]->(b)", {"a": name, "b": target})
            edges += 1
    heading = None
    for line in text.splitlines():
        if line.startswith("## "):
            heading = re.sub(r"\W", "_", line[3:].strip()).upper()
        elif line.startswith("> ") and heading:
            db.execute(f"MATCH (a {{name: $a}}) CREATE (a)-[:{heading}]->(:Sentence {{text: $t}})", {"a": name, "t": line[2:].strip()})
            sentences += 1
db.flush()
print(f"{len(notes)} notes, {edges} links, {sentences} sentences -> {OUT} "
      f"({db.node_count()} nodes, {db.relationship_count()} relationships, {time.time()-t:.1f}s)")
