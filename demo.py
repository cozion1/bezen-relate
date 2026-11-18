# One command for judges: builds the Relate graph from the sample vault, adds the meaning index,
# and runs both demos (memory of a person across messages, and reading one message).
# Usage: python demo.py            (works offline after the first model download; no API key needed)
#        ANTHROPIC_API_KEY=... python demo.py   (adds the agent step: trait + state + a quote checked in code)
import os, subprocess, sys

PY = sys.executable
HERE = os.path.dirname(os.path.abspath(__file__))
def run(*args):
    print(f"\n$ python {' '.join(args)}", flush=True)
    subprocess.run([PY, *args], cwd=HERE, check=True, env={**os.environ, "PYTHONIOENCODING": "utf-8"})

# sample_vault/ (32 public traits) ships with the repo; make_sample_vault.py is how it was built from bezenai.com/strengths
run("vault_to_graph.py", "sample_vault", "bezen.rl")   # vault -> Relate graph (nodes, typed edges, sentences)
run("index_anchors.py", "bezen.rl")               # every line of every trait -> Anchor node + Relate vector index
run("customer_memory.py", "bezen.rl", "--meaning")    # one person, three messages, what keeps coming back
run("read_person.py", "שוב הסכמתי לעזור לכולם בסוף השבוע, ועכשיו אין לי כוח לכלום. למה אני לא מסרב?", "bezen.rl")
