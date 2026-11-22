import json
from ke_recognizers import build_ke_analyzer

CONFIGS = [("neither fix", False, False), ("spaced IDs only", True, False),
           ("caps handling only", False, True), ("both fixes", True, True)]
SETS = {"large": "data/records_large.json", "held-out": "data/records_heldout.json"}

print(f"{'dataset':9}{'config':20}{'IDs exact':>11}{'names exact':>13}{'ID false pos':>14}")
for set_name, path in SETS.items():
    records = json.load(open(path, encoding="utf-8"))
    for cfg, spaced, caps in CONFIGS:
        analyzer = build_ke_analyzer(spaced=spaced, caps=caps)
        ids = names = ids_gold = names_gold = id_fp = 0
        for rec in records:
            text = rec["text"]
            preds = analyzer.analyze(text=text, language="en",
                                     entities=["KE_NATIONAL_ID", "PERSON"], score_threshold=0.4)
            spans = []
            for value, label in rec["entities"]:
                s = text.find(value)
                e = s + len(value)
                spans.append((s, e))
                hit = any(p.entity_type == label and p.start == s and p.end == e for p in preds)
                if label == "KE_NATIONAL_ID":
                    ids_gold += 1
                    ids += hit
                elif label == "PERSON":
                    names_gold += 1
                    names += hit
            id_fp += sum(1 for p in preds if p.entity_type == "KE_NATIONAL_ID"
                         and not any(s < p.end and p.start < e for s, e in spans))
        print(f"{set_name:9}{cfg:20}{ids:>6}/{ids_gold:<4}{names:>8}/{names_gold:<4}{id_fp:>14}")