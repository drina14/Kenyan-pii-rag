import json
from ke_recognizers import build_ke_analyzer

records = json.load(open("data/records_large.json", encoding="utf-8"))
total_ids = sum(1 for r in records for _, l in r["entities"] if l == "KE_NATIONAL_ID")

print(f"{'prefix':>6} {'suffix':>6} | {'IDs found':>9} | {'non-ID numbers flagged':>22}")
for prefix, suffix in [(3, 0), (3, 2), (3, 3), (5, 0), (5, 3)]:
    analyzer = build_ke_analyzer(prefix, suffix)
    found_ok, flagged_wrong = 0, 0
    for rec in records:
        text = rec["text"]
        gold = {v for v, l in rec["entities"] if l == "KE_NATIONAL_ID"}
        found = {
            text[p.start:p.end]
            for p in analyzer.analyze(
                text=text, language="en", entities=["KE_NATIONAL_ID"], score_threshold=0.4
            )
        }
        found_ok += len(gold & found)
        flagged_wrong += len(found - gold)
    print(f"{prefix:>6} {suffix:>6} | {found_ok:>4}/{total_ids:<4} | {flagged_wrong:>22}")