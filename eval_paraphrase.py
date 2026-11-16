# Honest check: messages written in DIFFERENT words from the strength sentences.
# Each case: (message, expected strength, expected state). Prints hit rate for strength and for strength+state.
# Usage: python eval_paraphrase.py [graph file] [matcher: trigram|vector]
import sys, importlib

from eval_paraphrase_cases import CASES

DB = sys.argv[1] if len(sys.argv) > 1 else "bezen.rl"
mode = sys.argv[2] if len(sys.argv) > 2 else "trigram"
sys.argv = [sys.argv[0], DB]
matcher = importlib.import_module("match_" + mode)

s_hits = full_hits = 0
for text, want_s, want_state in CASES:
    score, s, state, matched = matcher.read(text)
    ok_s, ok_full = s == want_s, s == want_s and state == want_state
    s_hits += ok_s; full_hits += ok_full
    print(f"{'V' if ok_full else ('~' if ok_s else 'X')}  want {want_s}/{want_state:<8}  got {s}/{state}  ({score:.2f})")
print(f"\n{mode}: strength {s_hits}/{len(CASES)}, strength+state {full_hits}/{len(CASES)}")
