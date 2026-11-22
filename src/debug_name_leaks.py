import json
from ke_recognizers import build_ke_analyzer

docs = {d["doc_id"]: d for d in json.load(open("data/corpus.json", encoding="utf-8"))}
analyzer = build_ke_analyzer()

for doc_id in ["AR-P09", "AR-P12", "RL-P01", "RL-P04", "AR-P01"]:
    text = docs[doc_id]["text"]
    print(f"\n{doc_id}: {text}")
    for r in analyzer.analyze(text=text, language="en", entities=["PERSON"], score_threshold=0.0):
        print(f"   PERSON detected: {text[r.start:r.end]!r} score={r.score:.2f}")