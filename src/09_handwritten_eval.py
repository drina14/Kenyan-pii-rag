import re
import sys
from collections import defaultdict
from ke_recognizers import build_ke_analyzer

LABEL = {"P": "PERSON", "ID": "KE_NATIONAL_ID", "PH": "PHONE_NUMBER"}
TAG = re.compile(r"\[\[(P|ID|PH)\|(.*?)\]\]")
PATH = next((a for a in sys.argv[1:] if a.endswith(".txt")), "data/handwritten.txt")

analyzer = build_ke_analyzer()
stats = defaultdict(lambda: defaultdict(int))
problems, notes = [], 0

for n, line in enumerate(open(PATH, encoding="utf-8"), 1):
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    notes += 1
    text, gold, pos = "", [], 0
    for m in TAG.finditer(line):
        text += line[pos:m.start()]
        start = len(text)
        text += m.group(2)
        gold.append((start, len(text), LABEL[m.group(1)], m.group(2)))
        pos = m.end()
    text += line[pos:]

    preds = analyzer.analyze(text=text, language="en", entities=list(LABEL.values()),
                             score_threshold=0.4)
    for s, e, label, value in gold:
        stats[label]["gold"] += 1
        same = [p for p in preds if p.entity_type == label]
        if any(p.start == s and p.end == e for p in same):
            stats[label]["exact"] += 1
        elif any(p.start <= s and p.end >= e for p in same):
            stats[label]["covered"] += 1
        elif any(s < p.end and p.start < e for p in same):
            stats[label]["partial"] += 1
            problems.append(f"  note {n}: '{value}' only PARTLY detected as {label} (part stays visible)")
        elif any(s < p.end and p.start < e for p in preds):
            stats[label]["wrong label"] += 1
            got = ", ".join(sorted({p.entity_type for p in preds if s < p.end and p.start < e}))
            problems.append(f"  note {n}: '{value}' expected {label}, got {got}")
        else:
            stats[label]["missed"] += 1
            problems.append(f"  note {n}: '{value}' ({label}) MISSED")
    for p in preds:
        if not any(s < p.end and p.start < e for s, e, _, _ in gold):
            stats[p.entity_type]["false positive"] += 1
            problems.append(f"  note {n}: FALSE POSITIVE '{text[p.start:p.end]}' as {p.entity_type}")

out = [f"{PATH}: {notes} lines | threshold 0.4 | Kenyan recognisers on",
       "Exact = same span. Covered = whole identifier inside a larger detection (e.g. title or 's included).",
       f"{'Entity':16}{'Gold':>6}{'Exact':>7}{'Covered':>9}{'Partial':>9}{'Wrong':>7}{'Missed':>8}{'FalsePos':>10}"]
for label in LABEL.values():
    s = stats[label]
    out.append(f"{label:16}{s['gold']:>6}{s['exact']:>7}{s['covered']:>9}{s['partial']:>9}"
               f"{s['wrong label']:>7}{s['missed']:>8}{s['false positive']:>10}")
out += ["", "Details:"] + (problems or ["  none"])
print("\n".join(out))