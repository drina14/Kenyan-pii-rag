from presidio_analyzer import AnalyzerEngine
from ke_recognizers import ke_national_id_recogniser

text = "Kevin Mwangi presented national ID 34567890 at reception. Receipt number 90817263."
a = AnalyzerEngine()
a.registry.add_recognizer(ke_national_id_recogniser())
for r in a.analyze(text=text, language="en", return_decision_process=True):
    if r.entity_type == "KE_NATIONAL_ID":
        print(text[r.start:r.end], r.score)
        print(r.analysis_explanation.textual_explanation, "\n")