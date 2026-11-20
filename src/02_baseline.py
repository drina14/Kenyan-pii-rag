import json
from collections import defaultdict
from presidio_analyzer import AnalyzerEngine

records = json.load(open("data/records.json", encoding="utf-8"))
import sys
from ke_recognizers import ke_national_id_recogniser

USE_KE = "--ke" in sys.argv
analyzer = AnalyzerEngine()
if USE_KE:
    analyzer.registry.add_recognizer(ke_national_id_recogniser())


def overlaps(a_start, a_end, b_start, b_end):
    return a_start < b_end and b_start < a_end


def evaluate(threshold):
    stats = defaultdict(lambda: {"gold": 0, "correct": 0, "misclassified": 0, "missed": 0})
    false_pos = defaultdict(int)
    problems = []

    for rec in records:
        text = rec["text"]
        preds = analyzer.analyze(text=text, language="en", score_threshold=threshold)

        gold = []
        for value, label in rec["entities"]:
            start = text.find(value)
            assert start != -1, f"Record {rec['id']}: '{value}' not found in text"
            gold.append((start, start + len(value), label, value))

        used = set()
        for s, e, label, value in gold:
            stats[label]["gold"] += 1
            hits = [(i, p) for i, p in enumerate(preds) if overlaps(s, e, p.start, p.end)]
            used.update(i for i, _ in hits)
            if any(p.entity_type == label for _, p in hits):
                stats[label]["correct"] += 1
            elif hits:
                stats[label]["misclassified"] += 1
                got = ", ".join(sorted({p.entity_type for _, p in hits}))
                problems.append(f"  rec {rec['id']}: '{value}' expected {label}, got {got}")
            else:
                stats[label]["missed"] += 1
                problems.append(f"  rec {rec['id']}: '{value}' expected {label}, MISSED")

        for i, p in enumerate(preds):
            if i not in used:
                false_pos[p.entity_type] += 1
                problems.append(
                    f"  rec {rec['id']}: FALSE POSITIVE '{text[p.start:p.end]}' as {p.entity_type} ({p.score:.2f})"
                )

    return stats, false_pos, problems


for threshold in (0.0, 0.4):
    stats, false_pos, problems = evaluate(threshold)
    print("=" * 60)
    name = "Default Presidio + Kenyan ID recogniser" if USE_KE else "Default Presidio"
    print(f"{name}, score threshold = {threshold}")
    print("=" * 60)
    print(f"{'Entity':18}{'Gold':>6}{'Correct':>9}{'Wrong label':>13}{'Missed':>8}")
    for label, s in stats.items():
        print(f"{label:18}{s['gold']:>6}{s['correct']:>9}{s['misclassified']:>13}{s['missed']:>8}")
    print("\nFalse positives (detections that match no labelled entity):")
    if false_pos:
        for label, n in false_pos.items():
            print(f"  {label}: {n}")
    else:
        print("  none")
    print("\nDetails:")
    print("\n".join(problems) if problems else "  none")
    print()