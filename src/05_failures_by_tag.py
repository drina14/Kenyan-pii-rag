import json
from collections import defaultdict
from ke_recognizers import build_ke_analyzer

records = json.load(open("data/records_large.json", encoding="utf-8"))
analyzer = build_ke_analyzer()

counts = defaultdict(lambda: defaultdict(int))
examples = {}

for rec in records:
    text = rec["text"]
    preds = analyzer.analyze(text=text, language="en", score_threshold=0.4)
    for value, label in rec["entities"]:
        if label != "KE_NATIONAL_ID":
            continue
        s = text.find(value)
        e = s + len(value)
        hits = [p for p in preds if s < p.end and p.start < e]
        if any(p.entity_type == "KE_NATIONAL_ID" for p in hits):
            outcome = "correct"
        elif hits:
            outcome = "wrong label: " + ", ".join(sorted({p.entity_type for p in hits}))
        else:
            outcome = "missed"
        counts[rec["tag"]][outcome] += 1
        if outcome != "correct":
            examples.setdefault((rec["tag"], outcome), text)

for tag, outcomes in counts.items():
    print(f"\n{tag}: {dict(outcomes)}")
for (tag, outcome), text in examples.items():
    print(f"\n[{tag} / {outcome}]\n  {text}")