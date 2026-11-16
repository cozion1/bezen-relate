# How often is the right strength inside the graph's shortlist (top 3 / top 5)?
import sys
sys.argv = [sys.argv[0], "-", sys.argv[1] if len(sys.argv) > 1 else "bezen.rl"]
import read_person
from eval_paraphrase_cases import CASES
h3 = h5 = 0
for text, want, _ in CASES:
    names = [c["strength"] for c in read_person.shortlist(text, 5)]
    h3 += want in names[:3]; h5 += want in names
    print(f"{'V' if want in names else 'X'}  {want:<14} -> {names}")
print(f"\nshortlist: top-3 {h3}/{len(CASES)}, top-5 {h5}/{len(CASES)}")
