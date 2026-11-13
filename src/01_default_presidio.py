import platform, sys
from importlib.metadata import version
from presidio_analyzer import AnalyzerEngine

print("Python:", sys.version.split()[0], "|", platform.system())
print("presidio-analyzer:", version("presidio-analyzer"))
print("presidio-anonymizer:", version("presidio-anonymizer"))
print("-" * 40)

text = (
    "Patient Wanjiru Kamau, national ID 12345678, "
    "phone +254 712 345 678, booked invoice number 87654321 "
    "for a follow-up visit."
)

analyzer = AnalyzerEngine()
results = analyzer.analyze(text=text, language="en")

for r in sorted(results, key=lambda r: r.start):
    print(f"{r.entity_type:15} {text[r.start:r.end]!r:25} score={r.score:.2f}")