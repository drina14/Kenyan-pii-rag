import hashlib
import hmac
import json
import re
import sys
from pathlib import Path

import anthropic
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from ke_recognizers import build_ke_analyzer

MODEL = "claude-haiku-5-5"
MAX_CALLS = 30
K = 3
DRY = "--dry" in sys.argv
CACHE = Path("data/answer_cache.json")  
SECRET = b"prototype-secret-key"
ENTITIES = ["PERSON", "PHONE_NUMBER", "KE_NATIONAL_ID"]

SYSTEM = (
    "You are an assistant for a clinic's staff. Answer ONLY from the context provided. "
    "Identifiers in the context appear as tokens such as PERSON_ab12cd; use them as written "
    "and never guess the real value. If the context does not contain the answer, say you "
    "cannot answer from the documents available to this user. Never give medical advice, "
    "diagnoses or treatment recommendations. Keep answers short."
)

docs = json.load(open("data/corpus.json", encoding="utf-8"))
questions = json.load(open("data/questions.json", encoding="utf-8"))
analyzer = build_ke_analyzer()
anonymizer = AnonymizerEngine()


def pseudo_token(entity, value):
    if entity == "PERSON":
        words = re.sub(r"['’]s$", "", value.strip()).lower().split()
        words = [w.strip(".,") for w in words if w.strip(".,") not in ("dr", "")]
        return " ".join(
            "PERSON_" + hmac.new(SECRET, f"PERSON:{w}".encode(), hashlib.sha256).hexdigest()[:6]
            for w in words
        )
    norm = "".join(ch for ch in value if ch.isdigit())
    return f"{entity}_" + hmac.new(SECRET, f"{entity}:{norm}".encode(), hashlib.sha256).hexdigest()[:6]


ops = {e: OperatorConfig("custom", {"lambda": (lambda v, e=e: pseudo_token(e, v))}) for e in ENTITIES}


def pseudo(text):
    found = analyzer.analyze(text=text, language="en", entities=ENTITIES, score_threshold=0.4)
    return anonymizer.anonymize(text=text, analyzer_results=found, operators=ops).text


for d in docs:
    d["pseudo_text"] = pseudo(d["text"])

NAME_PARTS = {w.strip(".,").lower() for d in docs for v, l in d["entities"]
              if l == "PERSON" for w in v.split() if len(w.strip(".,")) > 2}
RAW_VALUES = [v for d in docs for v, l in d["entities"] if l != "PERSON"]


def prompt_leaks(text):
    low = text.lower()
    parts = sorted(p for p in NAME_PARTS if re.search(rf"\b{re.escape(p)}\b", low))
    raw = [v for v in RAW_VALUES if v in text]
    return parts, raw

def retrieve(role, query):
    allowed = [d for d in docs if role in d["allowed_roles"]]  
    vec = TfidfVectorizer()
    mat = vec.fit_transform([d["pseudo_text"] for d in allowed])
    sims = cosine_similarity(vec.transform([query]), mat)[0]
    return [allowed[i] for i in sims.argsort()[::-1][:K] if sims[i] > 0]


cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
client = None if DRY else anthropic.Anthropic()  
calls = in_tok = out_tok = checked = ok = leaky = 0
leak_log = []
lines = []

for q in questions:
    query = pseudo(q["question"])
    results = retrieve(q["role"], query)
    context = "\n\n".join(f"[{d['doc_id']}] {d['pseudo_text']}" for d in results)
    prompt = f"Context:\n{context}\n\nQuestion: {query}"

    lp, lr = prompt_leaks(prompt)
    if lp or lr:
        leaky += 1
        leak_log.append(f"{q['qid']}: name parts {lp} raw values {lr}")

    if DRY:
        print(f"{q['qid']}: about {(len(SYSTEM) + len(prompt)) // 4} input tokens")
        if q["qid"] == "Q01":
            print("\n--- example prompt ---\n" + prompt + "\n----------------------\n")
        continue

    if q["qid"] in cache:
        answer = cache[q["qid"]]["answer"]
    else:
        if calls >= MAX_CALLS:
            print("Call limit reached - raise MAX_CALLS if you really want more.")
            break
        msg = client.messages.create(
            model=MODEL, max_tokens=600, system=SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        answer = "".join(b.text for b in msg.content if b.type == "text").strip()
        calls += 1
        in_tok += msg.usage.input_tokens
        out_tok += msg.usage.output_tokens
        if not answer:
            print(f"{q['qid']}: no text returned (stop_reason={msg.stop_reason}) - not cached")
            answer = "(no text returned)"
        else:
            cache[q["qid"]] = {"answer": answer}
            CACHE.write_text(json.dumps(cache, indent=1), encoding="utf-8")

    note = ""
    if q["expected"] == "answer" and q["answer_contains"]:
        checked += 1
        hit = q["answer_contains"].lower() in answer.lower()
        ok += hit
        note = f"  contains expected string: {'YES' if hit else 'NO'}"
    lines.append(f"{q['qid']} [{q['role']} / expected: {q['expected']}]{note}\n"
                 f"  Q: {q['question']}\n  retrieved: {[d['doc_id'] for d in results]}\n"
                 f"  A: {answer}\n")

leak_text = (f"Prompts containing a real name part or raw identifier: {leaky}/{len(questions)}\n"
             + "\n".join(leak_log))
print("\n" + leak_text)

if not DRY:
    summary = (f"Answers containing the expected string: {ok}/{checked}\n"
               f"New API calls this run: {calls} | input tokens: {in_tok} | output tokens: {out_tok}\n"
               "Deny and out_of_scope answers need MANUAL review: did the model reveal or advise anything?")
    text = summary + "\n\n" + leak_text + "\n\n" + "\n".join(lines)
    print(text)
    Path("results_25_answers.txt").write_text(text, encoding="utf-8")