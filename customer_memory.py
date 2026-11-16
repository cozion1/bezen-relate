# Graph memory of what a person keeps coming back to, across messages.
# Each message is read against the strength sentences (lack / balanced / excess) and stored as
#   (:Person)-[:WROTE]->(:Message)-[:READS_AS {state, score}]->(:Strength)
# so an agent can ask: "across everything this person said, which strength keeps showing, and in which state?"
# Usage: python customer_memory.py [graph file]
import re, sys, relate

DB = sys.argv[1] if len(sys.argv) > 1 else "bezen.rl"
db = relate.Database(DB)
rows = lambda r: r.data() if callable(r.data) else r.data

# Sample conversation (made up, public). Three messages from one person over a week.
MESSAGES = [
    ("Dana", "2026-11-10", "אני לא יכולה להחליט בלי ניתוח מלא, גם על דברים קטנים. תשלחו לי את כל הנתונים."),
    ("Dana", "2026-11-12", "שוב אין לי נתונים, אז אני לא יכולה לקבל שום עמדה על ההצעה שלכם."),
    ("Dana", "2026-11-15", "עברתי על המספרים. אפשר להחליט גם עם מידע חלקי, רק תגידו לי מה חסר."),
]

grams = lambda s: {s[i:i + 3] for i in range(len(s) - 2)} if s else set()
norm = lambda s: re.sub(r"[^\w ]", "", s)

def read(text):
    """Closest strength sentence by character trigrams (works for Hebrew without a stemmer)."""
    g = grams(norm(text))
    best = None
    for state in ("LACK", "BALANCED", "EXCESS"):
        for r in rows(db.execute(f"MATCH (s:Strength)-[:{state}]->(x:Sentence) RETURN s.name AS s, x.text AS t")):
            h = grams(norm(r["t"]))
            score = len(g & h) / (len(g | h) or 1)
            if not best or score > best[0]:
                best = (score, r["s"], state.lower(), r["t"])
    return best

db.execute("MATCH (m:Message) DETACH DELETE m")
db.execute("MATCH (p:Person) DETACH DELETE p")
for who, day, text in MESSAGES:
    score, strength, state, matched = read(text)
    db.execute("MERGE (:Person {name: $w})", {"w": who})
    db.execute("""MATCH (p:Person {name: $w}), (s:Strength {name: $s})
                  CREATE (p)-[:WROTE]->(m:Message {text: $t, day: $d})-[:READS_AS {state: $st, score: $sc, matched: $mt}]->(s)""",
               {"w": who, "s": strength, "t": text, "d": day, "st": state, "sc": round(score, 2), "mt": matched})
db.flush()

print("Per message:")
for r in rows(db.execute("""MATCH (p:Person)-[:WROTE]->(m:Message)-[r:READS_AS]->(s:Strength)
                            RETURN m.day AS day, s.name AS strength, r.state AS state, r.score AS score ORDER BY day""")):
    print(f"  {r['day']}  {r['strength']:<16} {r['state']:<9} {r['score']}")

print("\nWhat keeps coming back, and the next helpful sentence:")
for r in rows(db.execute("""MATCH (p:Person)-[:WROTE]->(m:Message)-[r:READS_AS]->(s:Strength)-[:DOMAIN]->(d:Domain)
                            WITH p, s, d, count(m) AS times, collect(r.state) AS states
                            ORDER BY times DESC LIMIT 1
                            MATCH (s)-[:BALANCED]->(b:Sentence)
                            RETURN p.name AS person, s.title AS strength, d.name AS domain, times, states, b.text AS balanced""")):
    print(f"  {r['person']}: {r['strength']} [{r['domain']}], {r['times']} messages, states {r['states']}")
    print(f"  balanced: {r['balanced']}")
