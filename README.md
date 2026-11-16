# BEZEN on Relate: a graph memory of what a person keeps coming back to

Agents remember facts. They don't remember the person. A customer who asks for "all the data" on Monday, says "I have no data, I can't decide" on Wednesday and "partial info is fine, tell me what's missing" on Friday is the same person working through the same strength: from too much, to too little, toward balance. Each message on its own looks unrelated. In a graph, it's one path.

This project loads a human-traits knowledge base (an Obsidian vault) into **Relate**, Neo4j's embedded graph database, and uses it as connected context for an agent:

1. **`make_sample_vault.py`** builds a public sample vault: 32 strengths, each with a domain and three states (lack / balanced / excess) and a sentence for each state.
2. **`vault_to_graph.py`** loads *any* Obsidian vault into one Relate file: notes become nodes, `key:: [[x]]` fields become typed edges, plain `[[x]]` become `LINKS`, and quoted lines under a heading become `Sentence` nodes.
3. **`customer_memory.py`** reads each message from a person against the sentences, stores `(:Person)-[:WROTE]->(:Message)-[:READS_AS {state}]->(:Strength)`, and asks the graph which strength keeps coming back and what the balanced next sentence is.

```
Per message:
  2026-11-10  Evidence Seeker  excess    0.52
  2026-11-12  Evidence Seeker  lack      0.44
  2026-11-15  Evidence Seeker  balanced  0.19

What keeps coming back, and the next helpful sentence:
  Dana: Evidence Seeker [Thinking], 3 messages
```

## Run

```bash
pip install relate-db
python make_sample_vault.py
python vault_to_graph.py sample_vault bezen.rl
python customer_memory.py bezen.rl
```

## What is public and what is not

The sample vault holds only the 32 strengths already published at bezenai.com/strengths. The full BEZEN pattern library stays private: the same loader runs on it locally, and nothing from it is in this repository.

## Status

Work in progress for the Relate by Neo4j Hackathon (started 2026-11-16). Matching is character trigrams for now; vector search in Relate is the next step.
