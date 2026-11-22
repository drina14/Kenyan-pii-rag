import re
from ke_recognizers import build_ke_analyzer

TAG = re.compile(r"\[\[(P|ID|PH)\|(.*?)\]\]")
analyzer = build_ke_analyzer()
WANT = {3, 7, 8, 14}

for n, line in enumerate(open("data/handwritten.txt", encoding="utf-8"), 1):
    if n not in WANT:
        continue
    text = TAG.sub(lambda m: m.group(2), line.strip())
    print(f"\nnote {n}: {text}")
    res = analyzer.analyze(text=text, language="en", entities=["KE_NATIONAL_ID"],
                           score_threshold=0.0, return_decision_process=True)
    if not res:
        print("   nothing matched at all")
    for r in res:
        ctx = r.analysis_explanation.supportive_context_word or "none"
        print(f"   {text[r.start:r.end]!r:14} score={r.score:.2f}  context word: {ctx}")