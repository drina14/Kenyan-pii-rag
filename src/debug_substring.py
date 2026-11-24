from ke_recognizers import build_ke_analyzer

analyzer = build_ke_analyzer()
tests = [
    "Invoice 45678912 remains open.",
    "Invoice 45678912 remains unpaid.",
    "Invoice 45678912 was paid.",
    "Invoice 45678912 is valid.",
    "Receipt 45678912 provided today.",
    "National ID 45678912 on file.",
]
for t in tests:
    res = analyzer.analyze(text=t, language="en", entities=["KE_NATIONAL_ID"],
                           score_threshold=0.0, return_decision_process=True)
    for r in res:
        word = r.analysis_explanation.supportive_context_word or "none"
        print(f"{t:38} score={r.score:.2f}  context word: {word}")