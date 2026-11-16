# Full two-step reading on the paraphrased cases: graph shortlist (top 5) + LLM pick with a verified quote.
# Needs ANTHROPIC_API_KEY. Usage: python eval_agent.py [graph file]
import sys
sys.argv = [sys.argv[0], "-", sys.argv[1] if len(sys.argv) > 1 else "bezen.rl"]
import read_person
from eval_paraphrase_cases import CASES

s_ok = full_ok = quotes = 0
for text, want_s, want_state in CASES:
    cands = read_person.shortlist(text, read_person.K)
    a = read_person.decide(text, cands) or {}
    ok_s = a.get("strength") == want_s
    ok_full = ok_s and a.get("state") == want_state
    s_ok += ok_s; full_ok += ok_full; quotes += bool(a.get("quote_verified"))
    print(f"{'V' if ok_full else ('~' if ok_s else 'X')}  want {want_s}/{want_state:<8} got {a.get('strength')}/{a.get('state')}"
          f"  quote {'ok' if a.get('quote_verified') else 'NOT FOUND'}")
print(f"\nagent: strength {s_ok}/{len(CASES)}, strength+state {full_ok}/{len(CASES)}, quotes verified {quotes}/{len(CASES)}")
