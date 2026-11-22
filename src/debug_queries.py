import json
from ke_recognizers import build_ke_analyzer

questions = json.load(open("data/questions.json", encoding="utf-8"))
analyzer = build_ke_analyzer()

for qid in ["Q01", "Q02", "Q03", "Q04", "Q05", "Q06", "Q07"]:
    q = next(x for x in questions if x["qid"] == qid)["question"]
    res = analyzer.analyze(text=q, language="en", entities=["PERSON"], score_threshold=0.0)
    found = [(q[r.start:r.end], round(r.score, 2)) for r in res]
    print(qid, q, "->", found or "no PERSON detected")