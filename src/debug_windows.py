import json
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.context_aware_enhancers import LemmaContextAwareEnhancer
from ke_recognizers import ke_national_id_recogniser

records = json.load(open("data/records.json", encoding="utf-8"))

for prefix in (5, 3, 2):
    enhancer = LemmaContextAwareEnhancer(context_prefix_count=prefix, context_suffix_count=0)
    analyzer = AnalyzerEngine(context_aware_enhancer=enhancer)
    analyzer.registry.add_recognizer(ke_national_id_recogniser())

    print(f"\n=== words checked before the number: {prefix} ===")
    for rec in records:
        text = rec["text"]
        gold_ids = [v for v, label in rec["entities"] if label == "KE_NATIONAL_ID"]
        found = [
            text[r.start:r.end]
            for r in analyzer.analyze(text=text, language="en", entities=["KE_NATIONAL_ID"], score_threshold=0.4)
        ]
        missed = [g for g in gold_ids if g not in found]
        extra = [f for f in found if f not in gold_ids]
        print(f"rec {rec['id']:>2}: found={found} missed={missed} wrongly_flagged={extra}")