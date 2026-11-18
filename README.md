# BEZEN on Relate: a graph memory of what a person keeps coming back to

Agents remember facts. They don't remember the person.

A customer writes on Monday *"I can't decide without a full analysis, send me all the data"*, on Wednesday *"I still have no data, so I can't take any position"*, and on Friday *"partial info is fine, just tell me what's missing"*. Three messages that look unrelated. In a graph they are one path: the same trait (Evidence Seeker), moving from **excess** to **lack** to **balance**. An agent that sees that path answers the person, not the sentence.

This project uses **Relate**, Neo4j's embedded graph database, as that memory.

## What it does

```
            sample_vault/  (Obsidian vault: 32 traits × lack / balanced / excess)
                 │  vault_to_graph.py
                 ▼
   (:Trait)-[:DOMAIN]->(:Domain)          (:Trait)-[:LACK|BALANCED|EXCESS]->(:Sentence)
                 │  index_anchors.py
                 ▼
   (:Trait)-[:ANCHOR]->(:Anchor {vec})   + Relate VECTOR INDEX anchor_vec
                 │  read_person.py / customer_memory.py
                 ▼
   (:Person)-[:WROTE]->(:Message)-[:READS_AS {state, score}]->(:Trait)
```

1. **Any Obsidian vault → one Relate file** (`vault_to_graph.py`). Notes become nodes, `key:: [[x]]` fields become typed edges, `[[x]]` become `LINKS`, quoted lines under a heading become `Sentence` nodes. The same loader runs on a private vault locally; only the public sample is in this repo.
2. **Meaning inside the graph** (`index_anchors.py`). Every line of every trait (how the person thinks, feels, acts, and the three states) becomes an `Anchor` node with a 384-dim vector from a small local multilingual model, indexed with Relate's `CREATE VECTOR INDEX`. No API needed.
3. **Two-step reading of a message** (`read_person.py`).
   - Step 1, the graph (free, local): one Cypher query — `db.index.vector.queryNodes` → closest anchors → their traits → ranked by the mean of the top-3 anchors, joined with each trait's domain and its lack / balanced / excess sentences.
   - Step 2, an agent (optional, needs `ANTHROPIC_API_KEY`): picks one trait and its state from the graph's candidates and must quote the person's own words; **the quote is checked in code** against the message.
4. **Memory of a person** (`customer_memory.py`). Each message is stored as `(:Person)-[:WROTE]->(:Message)-[:READS_AS {state}]->(:Trait)`, and one Cypher query answers: across everything this person said, which trait keeps showing, in which states, and what is the balanced next sentence.

## Run it

```bash
pip install -r requirements.txt
python demo.py
```

`demo.py` builds the graph, adds the vector index, and runs both demos. It works offline after the first download of the embedding model (~220 MB). With `ANTHROPIC_API_KEY` set, the agent step runs too.

Expected output (memory of a person):

```
Per message:
  2026-11-10  Evidence Seeker  excess
  2026-11-12  Evidence Seeker  lack
  2026-11-15  Evidence Seeker  balanced

What keeps coming back, and the next helpful sentence:
  Dana: Evidence Seeker [Thinking], 3 messages, states ['balanced', 'lack', 'excess']
```

## How it uses Relate

**Mode: single file.** The whole memory lives in one Relate file, `bezen.rl`, at the repo root. It is committed, so judges can open it without running anything: traits, domains, sentences, 705 anchors with the vector index, and Dana's three messages with their readings. `python demo.py` rebuilds it from `sample_vault/`.

Why single file: a person's memory should travel with the agent that serves them, like a document. One file can be copied, backed up, or kept on the user's own machine, and the private pattern library runs the same way locally without a server.

## How well it reads — measured, not claimed

`gen_cases.py` had a model write **288 everyday Hebrew messages** (3 per state × 32 traits), each in different words from the trait sentences; a lexical filter drops any that copy them. `eval_big.py` then checks trait **and** state:

| Method | trait + state correct | quotes verified |
|---|---|---|
| word overlap (trigrams) | ~20% (10-message set) | – |
| graph vector shortlist, top-8 + agent (Haiku) | 48% | 99% |
| graph shortlist, all 32 + agent (Haiku) | 77% | 99% |
| graph shortlist, all 32 + agent (Sonnet) | 83% | 99% |
| + full trait profile from the graph (Sonnet) | **84%** | **99%** |

What we learned: with 32 traits the agent should see all of them; the graph's real value is the **memory across messages** and the traceable path (message → anchor → trait → state → balanced sentence). The shortlist matters when the library is large (hundreds of patterns). The hardest state to read is *lack* (~75%).

## What is public and what is not

The sample vault holds only the 32 traits already published at [bezenai.com/strengths](https://bezenai.com/strengths). BEZEN's full pattern library is private; the same code runs on it locally and nothing from it is in this repository.

## Relate capabilities used

Embedded Python (`relate-db`), Cypher (`MATCH`, `MERGE`, `collect`, `reduce`, `OPTIONAL MATCH`), `vector()` values, `CREATE VECTOR INDEX`, `db.index.vector.queryNodes`, `vector.similarity.cosine`.

## Tools, AI use and earlier work (disclosure)

- **Naming:** BEZEN calls these *traits* (each with lack / balanced / excess). The evaluations above ran when the code still called them "strengths"; only the word changed, the data and method are the same.
- **Started** during the contest (first commit 16 Nov 2026).
- **Earlier own work reused:** the 32 public trait descriptions (bezenai.com) and the "exact quote checked in code" idea from earlier BEZEN projects. All code here was written during the contest.
- **Third party:** Relate (Apache-2.0), fastembed with `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, NumPy.
- **AI use:** the code was written with Claude (Anthropic) as a coding assistant; the 288 test messages were generated with Claude Sonnet; the optional agent step calls Claude Haiku / Sonnet.

## Files

| file | role |
|---|---|
| `vault_to_graph.py` | Obsidian vault → Relate graph |
| `index_anchors.py` | anchors + Relate vector index |
| `read_person.py` | two-step reading of one message |
| `customer_memory.py` | memory of a person across messages |
| `demo.py` | runs everything |
| `gen_cases.py`, `eval_big.py`, `eval_paraphrase*.py`, `eval_shortlist.py`, `eval_agent.py` | test sets and evaluations |
| `match_*.py` | earlier matchers kept for comparison |

License: MIT.
