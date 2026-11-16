# Honest check: messages written in DIFFERENT words from the strength sentences.
# Each case: (message, expected strength, expected state). Prints hit rate for strength and for strength+state.
# Usage: python eval_paraphrase.py [graph file] [matcher: trigram|vector]
import sys, importlib

CASES = [
    ("שוב הסכמתי לעזור לכולם בסוף השבוע, ועכשיו אין לי כוח לכלום. למה אני לא מסרב?", "Dependable", "excess"),
    ("שמישהו אחר יטפל בהזמנה, זה לא התפקיד שלי.", "Dependable", "lack"),
    ("הזזתם לי את הפגישה בעשר דקות וכל היום שלי התפרק.", "Order", "excess"),
    ("אצלי הכל בבלגן, אין סדר בניירת ואני לא מוצא כלום.", "Order", "lack"),
    ("אני יושב מול המשימה כבר שבוע ולא מזיז אצבע.", "Starter", "lack"),
    ("אני כבר באמצע העבודה, ואתם עדיין מדברים על תכנון?", "Starter", "excess"),
    ("כשהחברה שלי עצובה, אני נשאר שבור יומיים אחריה.", "Heart Reader", "excess"),
    ("לא אכפת לי מה העובדים מרגישים, שיביאו תוצאות.", "Heart Reader", "lack"),
    ("נכנסתי לישיבה ונתתי לכולם הוראות, גם למי שלא עובד אצלי.", "Take-Charge", "excess"),
    ("בדקתי שלוש פעמים ועדיין לא שלחתי, אולי יש טעות.", "Careful", "excess"),
]

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
