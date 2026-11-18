# Writes the validated sentences:
#   1. as an Obsidian vault: sentence_vault/<Strength>/<dimension>.md, every helpful sentence with its
#      lack and excess sentences under it, each marked ✅ verified or ⚠️ to review, with the model that wrote it;
#   2. into the Relate graph: (:Strength)-[:HELPFUL]->(:Helpful)-[:LACK_VERSION|EXCESS_VERSION]->(:Loaded).
# A separate folder: nothing is written into Cozio's own vault.
import json, os, re, sys, collections, relate

DB = sys.argv[1] if len(sys.argv) > 1 else "bezen.rl"
OUT = "sentence_vault"
DIM_HE = {"thoughts": "מחשבות", "emotions": "רגשות", "sensations": "תחושות",
          "behaviors": "התנהגויות מורכבות", "beliefs": "אמונות מגבילות", "blockers": "חסמים"}
rows = json.load(open("sentences_validated.json", encoding="utf-8"))
by_help = collections.defaultdict(list)
helpful = {}
for r in rows:
    if r["kind"] == "helpful": helpful[r["id"]] = r
    else: by_help[r["helpful_id"]].append(r)

mark = lambda r: "✅" if r["verified"] else "⚠️"
model = lambda r: r["model"].replace("claude-", "").split("-")[0]
tree = collections.defaultdict(lambda: collections.defaultdict(list))
for hid, h in helpful.items():
    tree[h["strength"]][h["dimension"]].append(h)

for s, dims in tree.items():
    os.makedirs(os.path.join(OUT, s), exist_ok=True)
    for dim, hs in dims.items():
        L = [f"# {s} – {DIM_HE[dim]}", "", f"strength:: [[{s}]]", f"dimension:: {DIM_HE[dim]}", ""]
        for h in hs:
            L += [f"## {mark(h)} {h['text']}", f"*מועיל · {model(h)}*", ""]
            for st, he in (("lack", "חסר"), ("excess", "מוגזם")):
                L.append(f"**{he}:**")
                for x in by_help.get(h["id"], []):
                    if x["state"] == st:
                        why = "" if x["verified"] else f" (הבודק: {x.get('v_state')} / {x.get('v_strength')})"
                        L.append(f"- {mark(x)} {x['text']} · {model(x)}{why}")
                L.append("")
        open(os.path.join(OUT, s, dim + ".md"), "w", encoding="utf-8").write("\n".join(L))

db = relate.Database(DB)
db.execute("MATCH (n:Helpful) DETACH DELETE n"); db.execute("MATCH (n:Loaded) DETACH DELETE n")
for h in helpful.values():
    db.execute("""MATCH (s:Strength {name: $s}) CREATE (s)-[:HELPFUL]->(:Helpful {id: $id, text: $t, dimension: $d,
                  model: $m, verified: $v})""", {"s": h["strength"], "id": h["id"], "t": h["text"], "d": h["dimension"],
                  "m": h["model"], "v": h["verified"]})
for hid, xs in by_help.items():
    for x in xs:
        rel = "LACK_VERSION" if x["state"] == "lack" else "EXCESS_VERSION"
        db.execute(f"""MATCH (h:Helpful {{id: $h}}) CREATE (h)-[:{rel}]->(:Loaded {{id: $id, text: $t, state: $st,
                       model: $m, verified: $v}})""", {"h": hid, "id": x["id"], "t": x["text"], "st": x["state"],
                       "m": x["model"], "v": x["verified"]})
db.flush()
v = sum(r["verified"] for r in rows)
print(f"vault: {sum(len(d) for d in tree.values())} notes in {OUT}/ ; graph: {len(helpful)} helpful, "
      f"{sum(len(x) for x in by_help.values())} loaded ; verified {v}/{len(rows)}")
