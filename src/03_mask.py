import json
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from ke_recognizers import build_ke_analyzer

records = json.load(open("data/records.json", encoding="utf-8"))
analyzer = build_ke_analyzer()
anonymizer = AnonymizerEngine()

ENTITIES = ["PERSON", "PHONE_NUMBER", "KE_NATIONAL_ID"]
operators = {e: OperatorConfig("replace", {"new_value": f"<{e}>"}) for e in ENTITIES}

lines = []
leaks = 0
for rec in records:
    text = rec["text"]
    found = analyzer.analyze(text=text, language="en", entities=ENTITIES, score_threshold=0.4)
    masked = anonymizer.anonymize(text=text, analyzer_results=found, operators=operators).text

    lines.append(f"--- Record {rec['id']} ---")
    lines.append("BEFORE: " + text)
    lines.append("AFTER:  " + masked)
    for value, label in rec["entities"]:
        if value in masked:
            leaks += 1
            lines.append(f"  LEAK: '{value}' ({label}) is still in the masked text")
    lines.append("")

total = sum(len(r["entities"]) for r in records)
lines.append(f"Labelled identifiers: {total} | still visible after masking: {leaks}")

output = "\n".join(lines)
print(output)
open("results_05_masking.txt", "w", encoding="utf-8").write(output)